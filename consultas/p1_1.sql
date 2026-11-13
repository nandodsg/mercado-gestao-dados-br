-- P1·1 · o núcleo é mesmo igual? % com intervalo de 95% (Wilson), por nível
with n as (
  select nivel, count(distinct id_publico) as n
  from mart_vaga_item where nivel in ('coordenador', 'gerente') group by nivel
), k as (
  select item, nivel, count(distinct id_publico) as k
  from mart_vaga_item where nivel in ('coordenador', 'gerente') group by item, nivel
), p as (
  select item, nivel, k, n, k / n as p from k join n using (nivel)
)
select item, nivel, k as vagas, n as base,
       round(100 * p) as pct,
       round(100 * (p + 1.96^2 / (2 * n) - 1.96 * sqrt(p * (1 - p) / n + 1.96^2 / (4 * n * n))) / (1 + 1.96^2 / n)) as ic_baixo,
       round(100 * (p + 1.96^2 / (2 * n) + 1.96 * sqrt(p * (1 - p) / n + 1.96^2 / (4 * n * n))) / (1 + 1.96^2 / n)) as ic_alto
from p
where item in (select item from p group by item having count(*) = 2 and min(p) >= 0.6)
order by min(pct) over (partition by item) desc, item, nivel;
