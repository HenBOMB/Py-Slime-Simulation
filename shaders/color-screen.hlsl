Texture2D<float4> trailMap : register(t0);
Texture2D<float4> agentsMap : register(t1);

RWTexture2D<float4> displayTexture : register(u0);
RWTexture2D<float4> agentsTexture : register(u1);

[numthreads(8,8,1)]
void main(uint3 tid : SV_DispatchThreadID)
{
	if(!DRAW_ONLY_AGENTS)
	{
		displayTexture[tid.xy] = agentsTexture[tid.xy];
		agentsTexture[tid.xy] = 0;
		return;
	}

	if(!DRAW_RAW)
	{
		displayTexture[tid.xy] = trailMap[tid.xy];
		agentsTexture[tid.xy] = 0;
		return;
	}

	float sum = 0;

	for (int x = -5; x <= 5; x++)
		for (int y = -5; y <= 5; y++)
			sum += trailMap[uint2(min(!WIDTH-1, max(0, tid.x + x)), min(!HEIGHT-1, max(0, tid.y + y))).xy].x;

	float sub = 100;
	float mask = max(sum - sub, 0) / (121 - sub);
	mask = saturate(mask);

	float4 color = !DRAW_COLOR;
	float4 color2 = saturate(color - .4);
	color2.a = 1;

	displayTexture[tid.xy] = lerp(0, color2, trailMap[tid.xy].r * trailMap[tid.xy].r);
	// displayTexture[tid.xy] = lerp(color2, color, trailMap[tid.xy].r) * trailMap[tid.xy].r;

	displayTexture[tid.xy] = lerp(displayTexture[tid.xy], displayTexture[tid.xy] * 2, mask);

	displayTexture[tid.xy] = saturate(displayTexture[tid.xy] + displayTexture[tid.xy] * agentsTexture[tid.xy]);

	agentsTexture[tid.xy] = agentsTexture[tid.xy] * (1 - !DECAY_RATE);
}