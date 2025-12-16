import os
import math
import pandas as pd

INPUT_FILES = {
    "material_types": "Material_type_import.xlsx",
    "product_types": "Product_type_import.xlsx",
    "workshops": "Workshops_import.xlsx",
    "products": "Products_import.xlsx",
    "product_workshops": "Product_workshops_import.xlsx",
}

OUT_DIR = "out_csv"

def make_id_map(values):
    # стабильные id: сортируем для повторяемости
    unique = sorted(pd.Series(values).dropna().astype(str).str.strip().unique())
    return {name: i + 1 for i, name in enumerate(unique)}

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # ---------- load ----------
    df_material = pd.read_excel(INPUT_FILES["material_types"])
    df_ptype = pd.read_excel(INPUT_FILES["product_types"])
    df_workshops = pd.read_excel(INPUT_FILES["workshops"])
    df_products = pd.read_excel(INPUT_FILES["products"])
    df_pw = pd.read_excel(INPUT_FILES["product_workshops"])

    # ---------- normalize strings ----------
    for df in [df_material, df_ptype, df_workshops, df_products, df_pw]:
        for c in df.columns:
            if df[c].dtype == "object":
                df[c] = df[c].astype(str).str.strip()

    # ---------- id maps ----------
    product_type_id = make_id_map(df_ptype["Тип продукции"])
    material_type_id = make_id_map(df_material["Тип материала"])
    workshop_id = make_id_map(df_workshops["Название цеха"])
    product_id = make_id_map(df_products["Наименование продукции"])

    # ---------- product_types.csv ----------
    out_ptype = pd.DataFrame({
        "id": [product_type_id[n] for n in sorted(product_type_id.keys())],
        "name": [n for n in sorted(product_type_id.keys())],
    })
    # подтягиваем коэффициент
    coef_map = dict(zip(df_ptype["Тип продукции"], df_ptype["Коэффициент типа продукции"]))
    out_ptype["coefficient"] = out_ptype["name"].map(coef_map).astype(float)
    out_ptype.to_csv(os.path.join(OUT_DIR, "product_types.csv"), index=False)

    # ---------- material_types.csv ----------
    out_m = pd.DataFrame({
        "id": [material_type_id[n] for n in sorted(material_type_id.keys())],
        "name": [n for n in sorted(material_type_id.keys())],
    })
    loss_map = dict(zip(df_material["Тип материала"], df_material["Процент потерь сырья"]))
    out_m["loss_percent"] = out_m["name"].map(loss_map).astype(float)
    out_m.to_csv(os.path.join(OUT_DIR, "material_types.csv"), index=False)

    # ---------- workshops.csv ----------
    out_w = pd.DataFrame({
        "id": df_workshops["Название цеха"].map(workshop_id).astype(int),
        "name": df_workshops["Название цеха"],
        "workshop_type": df_workshops["Тип цеха"],
        "people_count": df_workshops["Количество человек для производства "].astype(int),
    }).drop_duplicates(subset=["id"])
    out_w.to_csv(os.path.join(OUT_DIR, "workshops.csv"), index=False)

    # ---------- products.csv ----------
    out_p = pd.DataFrame({
        "id": df_products["Наименование продукции"].map(product_id).astype(int),
        "product_type_id": df_products["Тип продукции"].map(product_type_id).astype(int),
        "material_type_id": df_products["Основной материал"].map(material_type_id).astype(int),
        "name": df_products["Наименование продукции"],
        "article": df_products["Артикул"].astype(str),
        "min_partner_cost": df_products["Минимальная стоимость для партнера"].astype(float),
    }).drop_duplicates(subset=["id"])
    out_p.to_csv(os.path.join(OUT_DIR, "products.csv"), index=False)

    # ---------- product_workshops.csv ----------
    # Время в исходнике в часах (float). По ТЗ нужно целое число => переводим в минуты (int).
    def hours_to_minutes(x):
        if pd.isna(x):
            return 0
        return int(math.ceil(float(x) * 60))

    out_pw = pd.DataFrame({
        "product_id": df_pw["Наименование продукции"].map(product_id).astype(int),
        "workshop_id": df_pw["Название цеха"].map(workshop_id).astype(int),
        "time_minutes": df_pw["Время изготовления, ч"].apply(hours_to_minutes),
    })
    out_pw.to_csv(os.path.join(OUT_DIR, "product_workshops.csv"), index=False)

    print("OK. CSV saved to:", OUT_DIR)

if __name__ == "__main__":
    main()
