import { IsInt, Min } from 'class-validator';

export class ResubmitSkillVersionDto {
  @IsInt()
  @Min(1)
  version!: number;
}
