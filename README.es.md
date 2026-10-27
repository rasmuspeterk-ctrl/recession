# MOTOR v5.0.1 — probabilidad de inicio de una recesión en EE. UU.

[English](README.md) · **Español** · [中文](README.zh-CN.md) · [Français](README.fr.md) · [Dansk](README.da.md)

[![tests](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml/badge.svg)](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml)

## Qué es

MOTOR estima la probabilidad de que una recesión en EE. UU., fechada por el NBER, **comience dentro de los
próximos cuatro trimestres**. El modelo operativo usa una sola variable: la curva de rendimientos (bono del Tesoro
a 10 años menos letra a 3 meses), en una regresión logística con penalización L2. Todo se valida con un
*walk-forward* purgado de origen expansivo: en cada fecha histórica el modelo solo ve lo que se sabía entonces.
Solo se usan datos gratuitos (FRED, Reserva Federal, Shiller), y cada snapshot de datos se guarda con su hash.

## Cómo se mantiene honesto

- **Un registro prospectivo** ([LOG.md](LOG.md)): cada mes se anota una lectura *antes* de conocer el resultado,
  y las filas nunca se editan. Las reglas para puntuarlo se publicaron antes de la cuarta fila.
- **La lectura se compara siempre con la tasa base** (con qué frecuencia ha comenzado históricamente una recesión
  dentro de un año, unos 18 %). Si la incertidumbre del modelo incluye la tasa base, el veredicto es
  "no distinguible de la tasa base".
- **Se publica también lo que falló:** siete variables candidatas se probaron y se rechazaron, y figuran junto al
  modelo que sobrevivió.
- **Cifras con su incertidumbre:** la mejora de log-loss frente a la tasa base es de +20,4 % (sin oráculo, 219
  orígenes), pero su intervalo del 90 % empieza por debajo de cero. Detectar esa ventaja con un 80 % de potencia
  exigiría del orden de 150 años de registro.
- **Un consejo de modelos de lenguaje** debate y ratifica cada cambio de método; las decisiones se sellan antes de
  escribir el código ([RAADETS_SPEC7.md](RAADETS_SPEC7.md) y anteriores).

## Lectura actual

Última lectura registrada (2026-10-10): **P = 15,1 %** [10,4–21,6 %] frente a una tasa base del 18,0 %, es decir,
no distinguible de la tasa base. Una lectura intermedia del 2026-10-27 (no registrada) dio 14,8 %. El modelo lee
solo el nivel de la curva y no ve choques externos, por lo que esa cifra significa "en torno a la tasa base", no
"riesgo bajo".

## Más información

La documentación completa en inglés está en [README.md](README.md). La documentación técnica detallada, el
código y el registro están en danés; los textos operativos del consejo están en inglés. La página
[dashboard.html](dashboard.html) muestra la lectura actual.

Código bajo licencia MIT; textos propios bajo CC BY 4.0; los datos de terceros tienen sus propias condiciones
(véase [NOTICE.md](NOTICE.md)). El modelo no es una señal de trading ni asesoramiento de inversión.
