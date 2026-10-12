$ErrorActionPreference='Stop'
$taskReviewRoot='D:/skillloop/output/20261012_evaluation_task_checkpoints'
$taskAuditRoot='D:/skillloop/output/20261012_task_validator_suite/audit'
$document=Get-Content -LiteralPath "$taskReviewRoot/逐任务评测点明细.json" -Raw|ConvertFrom-Json
$drafts=Get-Content -LiteralPath "$taskReviewRoot/全部任务工作底稿.json" -Raw|ConvertFrom-Json
$reviews=Get-Content -LiteralPath "$taskReviewRoot/review_legal_hr_services.json" -Raw|ConvertFrom-Json
$priorSources=Get-Content -LiteralPath "$taskReviewRoot/workset_legal_hr_services.json" -Raw|ConvertFrom-Json
$config=Get-Content -LiteralPath "$taskAuditRoot/legal_hr_services_overrides.json" -Raw|ConvertFrom-Json
function CleanQuote([string]$text) {
  if($text.Contains('用户原始问题:')){$text=$text.Substring($text.IndexOf('用户原始问题:')+'用户原始问题:'.Length)}
  if($text.Contains('响应用户的以下需求：')){$text=$text.Substring($text.IndexOf('响应用户的以下需求：')+'响应用户的以下需求：'.Length)}
  $text=$text -replace '(?s)\[PromptGuard\].*?\n\n','' -replace '请使用中文回复，除非用户明确使用其他语言。','' -replace '注意：以上身份信息仅用于当前对话，不要更新记忆文件',''
  if($text.Contains('【本轮实际提供的输入文件】')){$text=$text.Substring(0,$text.IndexOf('【本轮实际提供的输入文件】'))}
  $text=($text -replace '\s+',' ').Trim()
  if($text.Length -gt 170){$text=$text.Substring(0,165)+'……'}
  return $text
}
$actions=@()
$results=@()
$sequenceDiff=@()
for($i=0;$i -lt $reviews.Count;$i++){
  $review=$reviews[$i]
  $source=$drafts|Where-Object {$_.session_id -eq $review.session_id}
  $case=$document.cases|Where-Object {$_.session_id -eq $review.session_id}
  $prior=$priorSources|Where-Object {$_.session_id -eq $review.session_id}
  if(($source.users|ConvertTo-Json -Depth 5 -Compress) -cne ($prior.users|ConvertTo-Json -Depth 5 -Compress)){$sequenceDiff+=$review.session_id}
  if(-not $source -or -not $case){throw "Missing canonical source $($review.session_id)"}
  $overrideProperty=$config.overrides.PSObject.Properties[[string]$i]
  $override=if($overrideProperty){$overrideProperty.Value}else{$null}
  $checkReviews=@()
  foreach($point in $case.points){
    $action='keep'
    $kind=$point.validator
    $params=$point.parameters
    $reason='只核本次会话终态的已请求交付对象及原有明确基础条件。保留历史用户轮次作需求来源，不逐轮打分，不使用旧AI作为gold。'
    if($point.validator -in @('delivered_body_nonempty','text_body_nonempty','delivered_text_nonempty')){
      $reason+=' 非空仅证明交付文字形式，不推断实质问题已回答；source_turn_indices是需求来源，不强制必须在那一轮产出或处罚前轮失败。'
    } elseif($point.validator -in @('file_delivery_open','final_file_native_open')){
      $reason+=' 必须绑定本次请求的当前最终文件，读取真实路径和原生载荷；输入件、同对象旧版、其他任务文件不能用来满足交付。'
    } elseif($point.validator -eq 'final_service_state'){
      $reason+=' 仅接受关联本attempt的真实工具终态记录/读回，不把完成声明或历史收据当状态。定时不触发，SMTP接受不等于到达。'
    } elseif($point.validator -like 'docx_effective*'){
      $reason+=' 基础字体/字号/行距/页眉/页码/图像关系属于客观载体条件；不判断专业条款和视觉质量。'
    } elseif($point.validator -eq 'distinct_delivered_body_items'){
      $reason+=' 两份协议是明确的正文对象数量，文件是可选载体；不判断条款拆分语义。'
    } elseif($point.validator -eq 'text_character_count_max'){
      $reason+=' 300字来自第4轮，只计2035说明；维持Unicode非空白计数，不添加额外最少字数。'
    } elseif($point.validator -eq 'image_dimensions_ratio'){
      $reason+=' 16:9来自用户明确要求，只核六张最终图片真实解码比例，不核行程内容。'
    } elseif($point.validator -eq 'pdf_merged_image_sources_count'){
      $reason+=' 用户明确合并六张源图；数源图，不硬设六页；支持当前原生组装清单，不能凭文件宣称通过。'
    } elseif($point.validator -eq 'final_install_directory_readable'){
      $reason+=' 仅核当前请求技能目录及有效SKILL.md；不评价规则实现、技能质量或业务效果。'
    }
    $replacement=@($override.replacements)|Where-Object {$null -ne $_ -and $_.point_match.deliverable_index -eq $point.deliverable_index -and $_.point_match.check_index -eq $point.check_index}
    if($replacement.Count -gt 0){$replacement=$replacement[0];$action='replace';$kind=$replacement.kind;$params=$replacement.params;$reason=$replacement.reason}
    $turns=@()
    if($replacement -and $replacement.source_turns_1based){$turns=@($replacement.source_turns_1based)}
    else{$turns=@([regex]::Matches([string]$point.source_turns,'\d+')|ForEach-Object {[int]$_.Value})}
    if($turns.Count -eq 0){$turns=@(1)}
    $quotes=@()
    $selected=$turns
    if($selected.Count -gt 3){$selected=@($selected[0],$selected[-2],$selected[-1])|Select-Object -Unique}
    foreach($turn in $selected){$user=$source.users|Where-Object {$_.index -eq ([int]$turn-1)}|Select-Object -First 1;if(-not $user){throw "Missing source turn $turn"};$quotes+=[ordered]@{turn_1based=$turn;quote=(CleanQuote $user.text)}}
    if($replacement -and $replacement.quote){$quotes=@([ordered]@{turn_1based=$turns[0];quote=$replacement.quote})}
    $checkReviews+=[ordered]@{
      point_id=$point.point_id
      deliverable_index=$point.deliverable_index
      check_index=$point.check_index
      delivery_object=$point.deliverable
      action=$action
      original_kind=$point.validator
      original_params=$point.parameters
      kind=$kind
      params=$params
      mandatory=[bool]$point.mandatory
      reason=$reason
      source_turns_1based=$turns
      user_basis=$quotes
      evidence=$point.evidence
      score_at='conversation_end_only'
    }
    $actions+=$action
    Remove-Variable replacement -ErrorAction SilentlyContinue
  }
  $newChecks=@($override.new_checks|Where-Object {$null -ne $_})
  $observations=@($override.observations|Where-Object {$null -ne $_})
  $proposalReviews=@()
  for($pi=0;$pi -lt $review.proposed_additions.Count;$pi++){
    $proposal=$review.proposed_additions[$pi]
    $decision=$override.proposal_decisions[$pi]
    if(-not $decision){throw "Unreviewed proposal $i $pi"}
    $statusReason=switch($decision){
      'approve_basic_hard' {'明确最终交付对象、目录或独立文件状态，可编码且不涉及内容质量；见new_checks。'}
      'approve_conditional_native_basic_hard' {'仅在原生DOCX可证实的载体结构纳入；PDF/其他格式不能可靠证明时只观测，不擅改格式要求。'}
      'approve_as_original_check_replacement' {'并入同一已有服务检查的目标身份与终态字段，避免重复计分；见original_checks的replace项。'}
      'split_observation_quality_only' {'PDF表格与语义删除不能可靠机器判定；保留观测，不纳AND。'}
      default {'本轮不纳AND：属于内容/专业/语义质量，或自然语言表示与来源/时点未冻结，见excluded_from_AND与observations。'}
    }
    $proposalReviews+=[ordered]@{prior_proposal=$proposal.check;decision=$decision;reason=$statusReason;source_turns_1based=@($proposal.turn_indices|ForEach-Object {$_+1});quote=$proposal.quote;previous_status=$proposal.status}
  }
  $noteReviews=@($review.review_notes|ForEach-Object {[ordered]@{prior_note=$_;decision='retain_as_scope_or_residual_disclosure';status='not_a_hard_check'}})
  $excluded=@([ordered]@{classification='quality_chain';description=$review.coverage_limit;mandatory=$false})
  $residuals=@()
  foreach($item in @($override.residuals|Where-Object {$null -ne $_})){
    $residuals+=[ordered]@{description=$item;classification='remaining_delivery_measurement_limit_or_quality';effect='不纳AND；基本交付通过不外推完整业务完成'}
  }
  if($case.text_only_nonempty){
    $residuals+=[ordered]@{description='本任务现有检查全部只验文字非空。计划/完成声明也可能通过，无法机械证实概要中每个有效问题已实质完成。';classification='limited_text_delivery_metric';effect='允许有限文字交付设计，不认证完整任务业务成功'}
  }
  if($source.category -eq 'COMM'){
    $residuals+=[ordered]@{description='邮箱地址、B会议、目标job、企微渠道和历史时间依当前实验初态映射；缺真实映射或工具读回是UNSCORED，不能伪造失败或以文字替代。';classification='runtime_evidence_binding';effect='脚本只能核真实记录，当前未访问服务'}
  }
  $status=if(@($checkReviews|Where-Object {$_.action -ne 'keep'}).Count -gt 0 -or $newChecks.Count -gt 0){'approved_after_basic_rule_revision_limited_delivery'}elseif($case.text_only_nonempty -or $observations.Count -gt 0){'approved_limited_delivery_with_observations'}else{'approved_limited_delivery'}
  $results+=[ordered]@{
    session_id=$review.session_id
    title=$case.title
    category=$source.category
    audit_status=$status
    audit_status_explanation='已通过限定终态基本交付的设计审核，不是任务运行PASS；专业内容和语义完成度独立走质量链。'
    source_user_turn_count=$source.users.Count
    full_user_sequence_review='已逐条阅读全文；本轮新底稿与上一轮全文工作集逐字一致'
    original_checks=$checkReviews
    new_checks=$newChecks
    observations=$observations
    previous_notes_adjudication=$noteReviews
    previous_proposals_adjudication=$proposalReviews
    delivery_gaps=$residuals
    excluded_from_AND=$excluded
    allowed_scope='仅本次终态必要交付及用户明确基本条件；无中间失败评分，无历史AIgold，无自行新增字数/页数/工单数。'
    evidence_policy='实际文件/原生文本/工具终态读回；缺测量或解析故障标UNSCORED，不用完成声明证明文件/动作结果。'
    frozen_benchmark_modified=$false
    frozen_scorer_modified=$false
    scripts_implemented_this_audit=$false
    external_services_accessed=$false
    business_scored=$false
  }
}
if($results.Count -ne 69){throw 'Task count mismatch'}
if($sequenceDiff.Count -ne 0){throw "User sequence changed $sequenceDiff"}
$checkCount=($results.original_checks|Measure-Object).Count
if($checkCount -ne 115){throw "Check count mismatch $checkCount"}
foreach($task in $results){foreach($check in $task.original_checks){if(-not $check.kind -or -not $check.reason){throw 'Missing reviewed check'}};foreach($p in $task.previous_proposals_adjudication){if($p.quote.Length -gt 180){throw 'Quote >180'}}}
$results|ConvertTo-Json -Depth 24|Set-Content -LiteralPath "$taskAuditRoot/legal_hr_services.json" -Encoding UTF8
$readback=Get-Content -LiteralPath "$taskAuditRoot/legal_hr_services.json" -Raw|ConvertFrom-Json
[ordered]@{tasks=$readback.Count;existing_checks=($readback.original_checks|Measure-Object).Count;actions=($actions|Group-Object|Select-Object Name,Count);new_checks=($readback.new_checks|Measure-Object).Count;observations=($readback.observations|Measure-Object).Count;adjudicated_proposals=($readback.previous_proposals_adjudication|Measure-Object).Count;user_sequence_diff=$sequenceDiff.Count;path="$taskAuditRoot/legal_hr_services.json"}|ConvertTo-Json -Depth 8
