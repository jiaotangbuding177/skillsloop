import { IsString, MaxLength } from 'class-validator';

export class SubmitSkillDto {
  @IsString()
  @MaxLength(120)
  skillKey!: string;
}
