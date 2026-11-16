# Inference optimisation: speed and accuracy per set-up

`python eval/exp_inference.py score`. Each row = one batch of real sheets marked with N sheets in flight.
*KV peak / queue peak*: highest KV-cache use and most requests waiting on the Gemma (A6000 or
wherever it runs) and Qwen servers during the batch. Steps and decisions: `INFERENCE_OPTIMIZATION.md`.

## Speed

| Set-up | Workload | In flight | Sheets | Wall | **Sheets / h** | Tokens / s | Gemma KV peak / queue | Qwen KV peak / queue | Errors |
|---|---|---|---|---|---|---|---|---|---|
| baseline | one-page | 16 | 30 | 55 s | **1950** | 2,667 | 99% / 1 | 49% / 9 | 0 |
| baseline | one-page | 32 | 30 | 48 s | **2249** | 3,014 | 100% / 12 | 93% / 2 | 0 |
| baseline | data-science | 16 | 48 | 1104 s | **156** | 1,824 | 100% / 50 | 99% / 37 | 0 |
| baseline | data-science | 32 | 48 | 1099 s | **157** | 1,817 | 100% / 128 | 100% / 84 | 0 |
| opt-lean | one-page | 16 | 30 | 51 s | **2111** | 2,828 | 97% / 4 | 14% / 8 | 0 |
| opt-lean | one-page | 32 | 30 | 48 s | **2226** | 2,896 | 100% / 12 | 25% / 0 | 0 |
| opt-lean | data-science | 16 | 48 | 1113 s | **155** | 1,796 | 100% / 65 | 45% / 39 | 0 |
| opt-lean | data-science | 32 | 48 | 1096 s | **158** | 1,836 | 100% / 121 | 89% / 86 | 0 |
| opt-swap | one-page | 16 | 30 | 110 s | **979** | 1,276 | 24% / 11 | 52% / 14 | 0 |
| opt-swap | one-page | 32 | 30 | 85 s | **1275** | 1,662 | 41% / 0 | 95% / 24 | 0 |
| opt-swap | data-science | 16 | 48 | 1261 s | **137** | 1,582 | 100% / 12 | 99% / 55 | 0 |
| opt-swap | data-science | 32 | 48 | 1309 s | **132** | 1,523 | 100% / 67 | 99% / 107 | 0 |
| opt-batch | one-page | 16 | 30 | 59 s | **1828** | 2,450 | 97% / 15 | 14% / 15 | 0 |
| opt-batch | one-page | 32 | 30 | 49 s | **2202** | 2,948 | 100% / 12 | 25% / 0 | 0 |
| opt-batch | data-science | 16 | 48 | 1131 s | **153** | 1,770 | 100% / 49 | 43% / 39 | 0 |
| opt-batch | data-science | 32 | 48 | 1123 s | **154** | 1,770 | 100% / 125 | 84% / 82 | 0 |
| opt-fp8kv | one-page | 16 | 30 | 50 s | **2172** | 2,973 | 100% / 5 | 13% / 11 | 0 |
| opt-fp8kv | one-page | 32 | 30 | 48 s | **2244** | 3,007 | 100% / 12 | 19% / 6 | 0 |
| opt-fp8kv | data-science | 16 | 48 | 1117 s | **155** | 1,795 | 100% / 53 | 34% / 42 | 0 |
| opt-fp8kv | data-science | 32 | 48 | 1106 s | **156** | 1,829 | 100% / 127 | 64% / 85 | 0 |
| lean-qwen1.4mp | one-page | 16 | 30 | 51 s | **2112** | 1,921 | 99% / 5 | 12% / 8 | 0 |
| lean-qwen1.4mp | one-page | 32 | 30 | 43 s | **2531** | 2,213 | 100% / 12 | 20% / 0 | 0 |
| lean-qwen1.4mp | data-science | 16 | 48 | 1111 s | **156** | 1,419 | 100% / 58 | 35% / 30 | 0 |
| lean-qwen1.4mp | data-science | 32 | 48 | 1106 s | **156** | 1,414 | 100% / 131 | 66% / 63 | 0 |
| lean-qwen1.0mp | one-page | 16 | 30 | 52 s | **2091** | 1,603 | 99% / 1 | 12% / 0 | 0 |
| lean-qwen1.0mp | one-page | 32 | 30 | 46 s | **2323** | 1,697 | 99% / 12 | 16% / 0 | 0 |
| lean-qwen1.0mp | data-science | 16 | 48 | 1107 s | **156** | 1,302 | 100% / 55 | 34% / 23 | 0 |
| lean-qwen1.0mp | data-science | 32 | 48 | 1104 s | **157** | 1,282 | 100% / 131 | 68% / 39 | 0 |
| lean-fixedfirst | data-science | 16 | 48 | 1047 s | **165** | 1,893 | 100% / 59 | 43% / 38 | 0 |
| lean-fixedfirst | data-science | 32 | 48 | 1008 s | **172** | 1,994 | 100% / 125 | 85% / 84 | 0 |
| opt-gemma2-fp8 | one-page | 16 | 30 | 59 s | **1843** | 2,401 | 46% / 0 | 82% / 11 | 0 |
| opt-gemma2-fp8 | one-page | 32 | 30 | 47 s | **2284** | 2,979 | 80% / 0 | 99% / 18 | 0 |
| opt-gemma2-fp8 | data-science | 16 | 48 | 839 s | **206** | 2,392 | 100% / 18 | 100% / 43 | 0 |
| opt-gemma2-fp8 | data-science | 32 | 48 | 795 s | **217** | 2,524 | 100% / 46 | 100% / 98 | 0 |

## Accuracy

*MCQ / numerical*: answers read correctly vs the labels. *Written MAE*: mean |our mark − teacher|
(0–2 per answer). *Same as baseline*: answers and marks identical to the baseline run with the same
workload and concurrency (the baseline against itself at another concurrency is the noise floor).

| Set-up | Workload | In flight | MCQ / numerical correct | Written MAE | TA items | Same as baseline |
|---|---|---|---|---|---|---|
| baseline | one-page | 16 | 205/225 (91.1%) | - | 8 | noise floor: 169/169 (100.0%) |
| baseline | one-page | 32 | 205/225 (91.1%) | - | 7 | noise floor: 169/169 (100.0%) |
| baseline | data-science | 16 | 937/960 (97.6%) | 0.650 | 6 | noise floor: 2129/2215 (96.1%) |
| baseline | data-science | 32 | 937/960 (97.6%) | 0.650 | 13 | noise floor: 2129/2215 (96.1%) |
| opt-lean | one-page | 16 | 205/225 (91.1%) | - | 7 | 169/169 (100.0%) |
| opt-lean | one-page | 32 | 205/225 (91.1%) | - | 7 | 169/169 (100.0%) |
| opt-lean | data-science | 16 | 937/960 (97.6%) | 0.647 | 6 | 2131/2215 (96.2%) |
| opt-lean | data-science | 32 | 937/960 (97.6%) | 0.644 | 17 | 2117/2215 (95.6%) |
| opt-swap | one-page | 16 | 203/225 (90.2%) | - | 5 | 168/169 (99.4%) |
| opt-swap | one-page | 32 | 203/225 (90.2%) | - | 5 | 168/169 (99.4%) |
| opt-swap | data-science | 16 | 936/960 (97.5%) | 0.642 | 19 | 2097/2214 (94.7%) |
| opt-swap | data-science | 32 | 936/960 (97.5%) | 0.646 | 17 | 2131/2215 (96.2%) |
| opt-batch | one-page | 16 | 205/225 (91.1%) | - | 7 | 169/169 (100.0%) |
| opt-batch | one-page | 32 | 205/225 (91.1%) | - | 7 | 169/169 (100.0%) |
| opt-batch | data-science | 16 | 937/960 (97.6%) | 0.645 | 7 | 2116/2214 (95.6%) |
| opt-batch | data-science | 32 | 937/960 (97.6%) | 0.647 | 9 | 2128/2215 (96.1%) |
| opt-fp8kv | one-page | 16 | 205/225 (91.1%) | - | 8 | 169/169 (100.0%) |
| opt-fp8kv | one-page | 32 | 205/225 (91.1%) | - | 7 | 169/169 (100.0%) |
| opt-fp8kv | data-science | 16 | 937/960 (97.6%) | 0.638 | 15 | 2099/2208 (95.1%) |
| opt-fp8kv | data-science | 32 | 938/960 (97.7%) | 0.644 | 18 | 2112/2208 (95.7%) |
| lean-qwen1.4mp | one-page | 16 | 206/225 (91.6%) | - | 11 | 168/169 (99.4%) |
| lean-qwen1.4mp | one-page | 32 | 205/225 (91.1%) | - | 7 | 169/169 (100.0%) |
| lean-qwen1.4mp | data-science | 16 | 938/960 (97.7%) | 0.650 | 15 | 1885/2183 (86.3%) |
| lean-qwen1.4mp | data-science | 32 | 938/960 (97.7%) | 0.648 | 11 | 1872/2181 (85.8%) |
| lean-qwen1.0mp | one-page | 16 | 205/225 (91.1%) | - | 11 | 169/169 (100.0%) |
| lean-qwen1.0mp | one-page | 32 | 205/225 (91.1%) | - | 6 | 169/169 (100.0%) |
| lean-qwen1.0mp | data-science | 16 | 937/960 (97.6%) | 0.656 | 23 | 1823/2187 (83.4%) |
| lean-qwen1.0mp | data-science | 32 | 938/960 (97.7%) | 0.655 | 22 | 1845/2190 (84.2%) |
| lean-fixedfirst | data-science | 16 | 937/960 (97.6%) | 0.671 | 14 | 2069/2214 (93.5%) |
| lean-fixedfirst | data-science | 32 | 937/960 (97.6%) | 0.673 | 21 | 2077/2216 (93.7%) |
| opt-gemma2-fp8 | one-page | 16 | 203/225 (90.2%) | - | 5 | 169/169 (100.0%) |
| opt-gemma2-fp8 | one-page | 32 | 206/225 (91.6%) | - | 6 | 166/166 (100.0%) |
| opt-gemma2-fp8 | data-science | 16 | 938/960 (97.7%) | 0.646 | 7 | 2081/2216 (93.9%) |
| opt-gemma2-fp8 | data-science | 32 | 937/960 (97.6%) | 0.639 | 15 | 2098/2207 (95.1%) |
