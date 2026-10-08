# Independent complete visual evaluation preparation

This version evaluates the immutable, completed v10 candidate with the official native `runner.run_agent --skip-agent` and official assertion VLM judge. It does not launch or modify an agent. Original v10 source, trajectory, freeze and SSIM-only score remain intact. Candidate snapshot SHA must be frozen before execution.

The official release lacks SSIM reference screenshots: v9 reported `no_gt_screenshots` on all 20 pages, visual0, weights functional0.5/visual0.5, making a 0.75 pass impossible even at perfect function. This is a missing visual measurement, not evidence of visual failure. VLM assertion scoring is an explicit separate protocol version, with actual API/error/inventory evidence required before accepting a complete result.

The VLM judge uses the authorized same-provider `deepseek-v4-flash-vision-exp` through the loopback relay. Same-provider self-judging and exact underlying checkpoint uncertainty must be disclosed; the single canary remains excluded from benchmark headline results. No old score is overwritten or called successful, and no benchmark answers enter the agent prompt.
