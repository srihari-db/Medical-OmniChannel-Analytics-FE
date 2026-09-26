# Evidence 04 — Gen AI pre-engagement briefing (live `ai_query` output)

The app grounds an `ai_query` call in the HCP's governed 360 context and asks the LLM
for a concise, non-promotional MSL briefing. Below is the **actual output** produced for
the top-priority HCP (HCP-00020, Dr. Priya Kim), generated via the SQL warehouse.

## Prompt (grounded in Gold context)
> You are an MSL assistant for a Daiichi Sankyo oncology Medical Affairs team. Using ONLY
> this context, write a concise 3-4 sentence, non-promotional pre-engagement briefing
> ending with a suggested discussion point. Context: `<gold_hcp_360 fields for HCP-00020>`

## Model output (`databricks-meta-llama-3-3-70b-instruct`)
> Dr. Priya Kim is a prominent Radiation Oncologist at UPMC Hillman with significant
> influence among her peers. Our previous interactions have focused on real-world evidence,
> safety management guidance, and comparative evidence, indicating her interest in practical
> applications of oncology treatments. With her recent inquiry on safety management guidance
> and interest in Perjeta, a competitor product, it's essential to re-engage and address any
> outstanding questions or concerns. What are her current challenges and unmet needs in
> managing safety for her patients, and how can we provide relevant evidence or support to
> address these gaps?

The briefing is fully grounded (institution, specialty, prior topics, open inquiry,
competitor interest all come from the governed context), non-promotional, and ends with a
suggested discussion point — exactly as instructed. No hallucinated data.
