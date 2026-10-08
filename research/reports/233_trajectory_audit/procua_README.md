---
language:
- en
license: cc-by-4.0
size_categories:
- 10K<n<100K
pretty_name: ProCUA-SFT
task_categories:
- image-text-to-text
tags:
- computer-use-agents
- gui-agents
- desktop-automation
- synthetic-data
- supervised-fine-tuning
- multimodal
- osworld
- pyautogui
---

# ProCUA-SFT

ProCUA-SFT is a large-scale synthetic trajectory dataset for training computer-use agents (CUAs): models that operate graphical desktop environments from screenshots using mouse, keyboard, and code-like actions. The dataset accompanies the **[ProCUA-SFT Technical Report](https://huggingface.co/papers/2606.17321)** and is designed for supervised fine-tuning of screenshot-based desktop agents.

This repository contains the raw trajectory artifacts used to construct those step-prefix SFT samples: trajectory JSON files and their corresponding screenshots. To keep the Hugging Face repository reliable for a dataset with millions of small files, trajectories are distributed as compressed tar shards under `shards/`.

## Dataset Summary

ProCUA-SFT was produced by an automated pipeline that uses a single VLM, Kimi-K2.5, in multiple roles: goal generation, precondition verification, and trajectory rollout. The pipeline synthesizes grounded desktop tasks, verifies that task preconditions hold before rollout, executes the task in a full desktop environment, and records screenshot-action trajectories.

The dataset is grounded in realistic desktop content and configurations, including:

- multi-application desktop configurations adapted from OSWorld;
- spreadsheet-grounded tasks using real-world spreadsheets from SpreadsheetBench as environment inputs;
- presentation-grounded tasks using permissively licensed Zenodo10K presentation files as environment inputs.

## Dataset Contents

The current release contains **93,566 raw trajectories**:

| Directory | Number of trajectories |
| --- | ---: |
| `part_1/` | 16,558 |
| `part_2/` | 59,096 |
| `part_3/` | 5,912 |
| `part_4/` | 12,000 |
| **Total** | **93,566** |

The four `part_*` directories are storage shards for organization and distribution. They should not be interpreted as train/validation/test splits.

On the Hub, the raw directories are packaged into approximately 50 `.tar.zst` files:

```text
README.md
ProCUA.pdf
manifest.jsonl
runs_manifest.jsonl
shards/
  procua_sft_00000.tar.zst
  procua_sft_00001.tar.zst
  ...
```

Each archive contains paths rooted at the original `part_*` directories, for example:

```text
part_1/
  <collection-run-id>/
    <trajectory-id>/
      trajectory.json
      0-1.png
      0-2.png
      ...
```

The accompanying `manifest.jsonl` lists each archive, its included parts, trajectory count, run count, and byte size. The `runs_manifest.jsonl` file maps each original collection-run directory to the shard that contains it.

To restore the raw directory tree locally:

```bash
mkdir procua_sft
cd procua_sft
for shard in /path/to/shards/part_*/*.tar.zst; do
  tar --use-compress-program=unzstd -xf "$shard"
done
```

After extraction, screenshot paths inside `trajectory.json` are relative to the restored dataset root, for example:

```text
part_4/cpu-0049--20260320_231802/0004/0-1.png
```

## Data Fields

Each `trajectory.json` is a JSON object with the following top-level fields:

- `trajectory_id`: trajectory identifier.
- `metadata`: environment and collection metadata, including VM image, screen size, OSWorld-style setup information, and pipeline metadata.
- `goal`: high-level natural-language task goal.
- `steps`: list of subgoal records.

Each step contains:

- `subgoal`: natural-language subgoal for the step group.
- `subgoal_intent`: intent annotation for the subgoal.
- `actions`: ordered action records.

Each action record may include:

- `screenshot`: relative path to the screenshot observed before the action.
- `pyautogui_command`: executable PyAutoGUI-style command string.
- `action_type`: action family, such as `pyautogui`.
- `action_generation`: structured model output containing thought/action/code fields.
- `raw_reasoning`: raw reasoning text produced during rollout.
- `raw_response`: raw action/code response produced during rollout.

## Licensing and Attribution

This dataset is released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

Source .pptx files used as grounding inputs are drawn from the Zenodo10K dataset (CC BY 4.0, Forceless/Zenodo10K on Hugging Face); original files were deposited on Zenodo by their respective authors under CC BY 4.0.

## Acknowledgments

ProCUA-SFT builds on desktop task environments and source content from OSWorld, SpreadsheetBench, and Zenodo10K, and uses Kimi-K2.5 for synthetic goal generation, precondition checking, and rollout.

## Citation

If you use this dataset, please cite:

```bibtex
@misc{jung2026procuasfttechnicalreport,
  title={ProCUA-SFT Technical Report},
  author={Jaehun Jung and Ximing Lu and Brandon Cui and Muhammad Khalifa and Shaokun Zhang and Hao Zhang and Jin Xu and Amala Sanjay Deshmukh and Karan Sapra and Andrew Tao and Yejin Choi and Jan Kautz and Mingjie Liu and Yi Dong},
  year={2026},
  eprint={2606.17321},
  archivePrefix={arXiv},
  primaryClass={cs.LG},
  url={https://arxiv.org/abs/2606.17321},
}
```
