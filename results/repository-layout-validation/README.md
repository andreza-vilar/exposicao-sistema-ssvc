# Verificação após reorganização

Executado localmente em 26/11/2026, com `.venv/bin/python`, ambiente limpo e launcher offline.

- `tests/run_all.py`: **47 testes aprovados**, em 0,281 s; [log](tests.txt).
- `scripts/run_scenarios.py`: **16/16**, saída idêntica ao final do CP02.1; [log](historical.txt).
- `src/run_experiments.py`: 16 B1, dez B2, dez pares e seis não aplicáveis, sem erros. Concordância histórica: B1 completo 13/16; B1 pareado 7/10; B2 pareado 10/10. [Rodada completa](experiments/summary.json).
- Matriz de transição, distribuições, concordâncias e direção das divergências conferidas contra `results/cp01.2/summary.json`, sem mudanças.
- SHA-256 do classificador histórico preservado: `923c98497639bd9a7a05c79f98a9a252c1b0ef840af985750c6eeb7c1eabec7b`.
- Os dois PDFs locais mantiveram seus hashes e foram movidos para `references/`, ignorado pelo Git.
- Links locais da documentação e do README conferidos, sem destinos ausentes.

Os testes não consultaram rede ou configurações corporativas. A única operação remota autorizada nesta tarefa é o push Git solicitado pelo usuário, separado da execução dos testes. Nenhuma regra de classificação ou rótulo histórico foi alterado.
