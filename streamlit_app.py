import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io

st.title("Vyhodnocení laboratorního deníku")

# Upload souborů
pdf_file = st.file_uploader("Nahraj laboratorní deník (PDF)", type="pdf")
xlsx_file = st.file_uploader("Nahraj PROMT.xlsx", type="xlsx")

if pdf_file and xlsx_file:
    # Načtení textu z PDF
    pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")
    lab_text = "\n".join(page.get_text() for page in pdf).lower()

    # Načtení Excelu
    xls = pd.ExcelFile(xlsx_file)
    pm_df = pd.read_excel(xls, sheet_name="PM")
    lm_df = pd.read_excel(xls, sheet_name="LM")
    op1_df = pd.read_excel(xls, sheet_name="seznam zkoušek PM+LM OP1 ")
    op2_df = pd.read_excel(xls, sheet_name="seznam zkoušek PM+LM OP2")

    # Získání mapování typů zásypů na staničení
    def build_mapping(typy_row, stanice_row):
        mapping = {}
        for col in typy_row.index:
            typ = typy_row[col]
            stanice = stanice_row[col]
            if pd.notna(typ) and pd.notna(stanice):
                mapping[typ.strip()] = stanice.strip()
        return mapping

    op1_mapping = build_mapping(op1_df.iloc[0], op1_df.iloc[2])
    op2_mapping = build_mapping(op2_df.iloc[0], op2_df.iloc[2])

    def count_tests(text, typ, staniceni):
        search = f"{typ.lower()} {staniceni.lower()}"
        return text.count(search)

    def vypln_skutecnosti(df):
        for i, row in df.iterrows():
            typ = row["Typ zásypu"]
            if pd.isna(typ):
                continue
            typ = typ.strip()
            if typ in op1_mapping:
                df.at[i, "Skutečnost OP1"] = count_tests(lab_text, typ, op1_mapping[typ])
            if typ in op2_mapping:
                df.at[i, "Skutečnost OP2"] = count_tests(lab_text, typ, op2_mapping[typ])
        return df

    st.subheader("Výsledky pro list PM")
    st.dataframe(vypln_skutecnosti(pm_df))

    st.subheader("Výsledky pro list LM")
    st.dataframe(vypln_skutecnosti(lm_df))

    # Uložení výsledků
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pm_df.to_excel(writer, index=False, sheet_name="PM")
        lm_df.to_excel(writer, index=False, sheet_name="LM")
        op1_df.to_excel(writer, index=False, sheet_name="seznam zkoušek PM+LM OP1 ")
        op2_df.to_excel(writer, index=False, sheet_name="seznam zkoušek PM+LM OP2")

    st.download_button(
        label="📥 Stáhnout výstupní Excel",
        data=output.getvalue(),
        file_name="vyhodnoceni_vystup.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
