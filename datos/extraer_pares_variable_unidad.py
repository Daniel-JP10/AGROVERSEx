# asistido por SI: Claude Code (Anthropic), extrae los pares (variable, unidad) de serie_mensual para la prueba de paraMostrar
import csv, glob, gzip, json, sys
carpeta, salida = sys.argv[1], sys.argv[2]
pares = set()
for f in sorted(glob.glob(f'{carpeta}/serie_mensual_*.csv.gz')):
    with gzip.open(f, 'rt', encoding='utf-8') as h:
        pares |= {(r['variable'], r['unidad']) for r in csv.DictReader(h)}
json.dump(sorted(pares), open(salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(sorted(pares))
