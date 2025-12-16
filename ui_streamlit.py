import streamlit as st
import requests

API = "http://127.0.0.1:2281"  # FastAPI

st.set_page_config(page_title="Меб 52", layout="wide")
st.title("Подсистема")
st.caption("© 2010–2025")

page = st.sidebar.radio("Раздел", ["Продукция", "Добавить продукт", "Цеха", "Расчёт сырья"])

def show_error(msg: str):
    st.error(msg)

def api_get(path: str):
    try:
        r = requests.get(API + path, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        show_error(f"Ошибка запроса: {e}")
        return None

def api_post(path: str, payload: dict):
    try:
        r = requests.post(API + path, json=payload, timeout=10)
        if r.status_code >= 400:
            try:
                st.error(f"Ошибка {r.status_code}: {r.json()}")
            except Exception:
                st.error(f"Ошибка {r.status_code}: {r.text}")
            return None
        return r.json()
    except Exception as e:
        show_error(f"Ошибка запроса: {e}")
        return None

# ======== Pages ========
if page == "Продукция":
    st.subheader("Просмотр списка продукции")
    data = api_get("/products")
    if data is not None:
        st.dataframe(data, use_container_width=True)

elif page == "Добавить продукт":
    st.subheader("Добавление продукции (с валидацией)")
    with st.form("create"):
        name = st.text_input("Наименование")
        article = st.text_input("Артикул")
        cost = st.number_input("Мин. стоимость партнёра", min_value=0.0, step=1.0)
        pt = st.number_input("product_type_id", min_value=1, step=1)
        mt = st.number_input("material_type_id", min_value=1, step=1)
        ok = st.form_submit_button("Добавить")

    if ok:
        if not name.strip():
            show_error("Введите наименование.")
        elif not article.strip():
            show_error("Введите артикул.")
        else:
            res = api_post("/products", {
                "name": name,
                "article": article,
                "min_partner_cost": float(cost),
                "product_type_id": int(pt),
                "material_type_id": int(mt),
            })
            if res is not None:
                st.success("Продукт добавлен")
                st.json(res)

elif page == "Цеха":
    st.subheader("Список цехов для продукции")
    product_id = st.number_input("product_id", min_value=1, step=1)
    if st.button("Показать"):
        data = api_get(f"/products/{int(product_id)}/workshops")
        if data is not None:
            st.dataframe(data, use_container_width=True)
        time_data = api_get(f"/products/{int(product_id)}/total-time")
        if time_data is not None:
            st.info(f"Итого: {time_data['total_time_minutes']} минут (~{time_data['total_time_hours_int']} ч)")

elif page == "Расчёт сырья":
    st.subheader("Расчёт количества сырья")
    pt = st.number_input("product_type_id", min_value=1, step=1)
    mt = st.number_input("material_type_id", min_value=1, step=1)
    count = st.number_input("Количество продукции", min_value=1, step=1)
    if st.button("Рассчитать"):
        data = api_post("/materials/calc", {"product_type_id": int(pt), "material_type_id": int(mt), "count": int(count)})
        if data is not None:
            st.success(f"Нужно сырья: {data['required_amount']}")
