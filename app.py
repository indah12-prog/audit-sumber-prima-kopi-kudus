
import json
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Audit PT Sumber Kopi Prima",
    page_icon="☕",
    layout="wide"
)

pertanyaan = json.loads(
    (Path(__file__).parent / "pertanyaan.json").read_text(
        encoding="utf-8"
    )
)

pilihan = ["Belum dijawab", "Ya", "Tidak", "N/A"]

st.title("☕ Form Audit Sistem Informasi")
st.subheader("PT Sumber Kopi Prima")
st.caption(
    "COBIT 5 | Indah Chusnul Febriani | 202453126 | Kelas D"
)

st.info(
    "Isi jawaban berdasarkan pemeriksaan. "
    "Cantumkan bukti untuk jawaban Ya dan alasan untuk N/A."
)

with st.form("form_audit"):
    st.header("Identitas Audit")

    kiri, kanan = st.columns(2)

    with kiri:
        perusahaan = st.text_input(
            "Nama perusahaan", "PT Sumber Kopi Prima"
        )
        auditor = st.text_input(
            "Nama auditor", "Indah Chusnul Febriani"
        )
        periode = st.text_input("Periode audit")
        tanggal = st.date_input("Tanggal audit", date.today())
        unit = st.text_input(
            "Unit atau bagian", "Pengelolaan Sistem Informasi"
        )

    with kanan:
        narasumber = st.text_input("Nama narasumber")
        jabatan = st.text_input("Jabatan narasumber")
        objek = st.text_input(
            "Objek audit",
            "Tata kelola dan manajemen sistem informasi"
        )
        sistem = st.text_input(
            "Sistem yang diperiksa",
            "Pengelolaan Sistem Informasi dan Teknologi Informasi Perusahaan"
        )
        tujuan = st.text_input(
            "Tujuan pemeriksaan",
            "Mengevaluasi pengelolaan sistem informasi berdasarkan domain COBIT 5"
        )

    st.header("Pertanyaan Audit")

    tab_domain = st.tabs(list(pertanyaan))
    baris = []

    for tab, (domain, daftar) in zip(
        tab_domain, pertanyaan.items()
    ):
        with tab:
            for nomor, (kode, teks) in enumerate(
                daftar, start=1
            ):
                # ID terpisah karena kode proses dapat berulang.
                id_pertanyaan = f"{domain}-{nomor}"

                st.markdown(f"**{nomor}. {kode}**")
                st.write(teks)

                jawaban = st.radio(
                    "Jawaban",
                    pilihan,
                    horizontal=True,
                    key=f"jawaban_{id_pertanyaan}"
                )

                bukti = st.text_area(
                    "Bukti / catatan auditor / alasan N/A",
                    key=f"bukti_{id_pertanyaan}"
                )

                baris.append({
                    "ID": id_pertanyaan,
                    "Domain": domain,
                    "Kode Proses": kode,
                    "Pertanyaan": teks,
                    "Jawaban": jawaban,
                    "Bukti/Catatan": bukti
                })

                st.divider()

    proses = st.form_submit_button(
        "Proses Hasil Audit",
        type="primary"
    )

if proses:
    identitas = {
        "Perusahaan": perusahaan,
        "Framework": "COBIT 5",
        "Auditor": auditor,
        "Periode": periode,
        "Tanggal": str(tanggal),
        "Unit": unit,
        "Narasumber": narasumber,
        "Jabatan": jabatan,
        "Objek Audit": objek,
        "Sistem": sistem,
        "Tujuan": tujuan
    }

    st.session_state["hasil"] = pd.DataFrame([
        {**identitas, **item} for item in baris
    ])

if "hasil" in st.session_state:
    df = st.session_state["hasil"]

    st.header("Hasil Audit")
    st.caption(
        "Hasil mengikuti isian terakhir yang diproses. "
        "Setelah mengubah form, tekan Proses Hasil Audit kembali."
    )

    belum = int((df["Jawaban"] == "Belum dijawab").sum())

    st.progress(
        (30 - belum) / 30,
        text=f"{30 - belum}/30 pertanyaan dijawab"
    )

    if belum:
        st.warning(
            f"{belum} pertanyaan belum dijawab. "
            "Rekapitulasi masih sementara."
        )

    tanpa_bukti = df[
        df["Jawaban"].isin(["Ya", "N/A"])
        & df["Bukti/Catatan"].str.strip().eq("")
    ]

    if not tanpa_bukti.empty:
        st.warning(
            "Lengkapi bukti jawaban Ya atau alasan N/A: "
            + ", ".join(tanpa_bukti["ID"])
        )

    rekap = pd.crosstab(df["Domain"], df["Jawaban"])
    rekap = rekap.reindex(
        index=list(pertanyaan),
        columns=pilihan,
        fill_value=0
    )

    rekap["Jumlah Pertanyaan"] = rekap[pilihan].sum(axis=1)

    pembagi = rekap["Ya"] + rekap["Tidak"]

    rekap["Persentase Ya (%)"] = [
        round(100 * ya / total, 2) if total else None
        for ya, total in zip(rekap["Ya"], pembagi)
    ]

    st.subheader("Rekapitulasi per Domain")
    st.dataframe(rekap, use_container_width=True)

    st.subheader("Grafik Jawaban")
    st.bar_chart(rekap[pilihan])

    ya = int((df["Jawaban"] == "Ya").sum())
    tidak = int((df["Jawaban"] == "Tidak").sum())

    st.metric(
        "Persentase Ya keseluruhan",
        f"{100 * ya / (ya + tidak):.2f}%"
        if ya + tidak else "Tidak dapat dihitung"
    )

    st.caption(
        "Rumus: Ya ÷ (Ya + Tidak) × 100%. "
        "N/A dan Belum dijawab dikeluarkan dari pembagi. "
        "Persentase ini bukan tingkat kapabilitas resmi COBIT 5."
    )

    def buat_csv(tabel):
        ekspor = tabel.copy()

        def amankan(nilai):
            if isinstance(nilai, str):
                if nilai.lstrip().startswith(("=", "+", "-", "@")):
                    return "'" + nilai
            return nilai

        for kolom in ekspor.columns:
            ekspor[kolom] = ekspor[kolom].map(amankan)

        return ekspor.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "Unduh Jawaban CSV",
        data=buat_csv(df),
        file_name="hasil_audit_sumber_kopi_prima.csv",
        mime="text/csv"
    )

    st.download_button(
        "Unduh Rekap CSV",
        data=buat_csv(rekap.reset_index()),
        file_name="rekap_audit_sumber_kopi_prima.csv",
        mime="text/csv"
    )

st.caption(
    "Data tersimpan sementara dalam sesi. "
    "Unduh hasil sebelum menutup atau memuat ulang halaman."
)
