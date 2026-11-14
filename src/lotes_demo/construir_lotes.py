# asistido por SI: Claude Code, construye lotes_demo.json desde las opciones de la Parte A (T-D5 Parte B)
import json
from pathlib import Path

OPC = Path("C:/NASA/AGROVERSEx/repo/Docu/datos/T-D5_opciones_lotes.geojson")
SALIDA = Path(__file__).resolve().parents[2] / "datos" / "lotes" / "lotes_demo.json"

# decisiÃ³n del director: USA-A y COL-A; clima_tipo segÃºn el ejemplo de Ipiales del Gemelo
LOTES = {
    "DEMO-USA-01": dict(opcion="DEMO-USA-A", nombre="Lote DEMO Saunders (Nebraska)", clima_tipo="templado",
                        estacion="GHCN-Daily USC00255362 MEAD 6S"),
    "DEMO-COL-01": dict(opcion="DEMO-COL-A", nombre="Lote DEMO Ipiales (NariÃ±o)", clima_tipo="tropical",
                        estacion="GHCN-Daily COM00080370 SAN LUIS"),
}


def area_ha(anillo, lat):
    # área en UTM de la zona del lote (el polígono redondeado a 3 decimales difiere del original de la Parte A)
    from pyproj import Transformer
    from shapely.geometry import Polygon
    from shapely.ops import transform
    zona = int((anillo[0][0] + 180) // 6) + 1
    t = Transformer.from_crs(4326, (32600 if lat >= 0 else 32700) + zona, always_xy=True).transform
    return round(transform(t, Polygon(anillo)).area / 1e4, 1)


def main():
    feats = {f["properties"]["opcion"]: f for f in json.loads(OPC.read_text(encoding="utf-8"))["features"]}
    out = []
    for lid, c in LOTES.items():
        f = feats[c["opcion"]]
        p = f["properties"]
        anillo = [[round(x, 3), round(y, 3)] for x, y in f["geometry"]["coordinates"][0]]
        out.append(dict(lote_id=lid, unidad_id=p["unidad_id"], nombre=c["nombre"], etiqueta="DEMO",
                        clima_tipo=c["clima_tipo"], lat=round(p["centro_lat"], 3), lon=round(p["centro_lon"], 3),
                        area_ha=area_ha(anillo, p["centro_lat"]), area_ha_parte_a=p["area_ha_aprox"], estacion_referencia=c["estacion"],
                        geometria={"type": "Polygon", "coordinates": [anillo]},
                        nota="Lote DEMO ilustrativo sobre pixeles agricolas; no es una finca identificada"))
    SALIDA.write_text(json.dumps({"version": 1, "lotes": out}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
