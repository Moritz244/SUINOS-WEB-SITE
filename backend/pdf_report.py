"""PDF viability report generator for AquaSuíno."""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


EMERALD = colors.HexColor("#059669")
AQUA = colors.HexColor("#0284C7")
DARK = colors.HexColor("#0F172A")
GRAY = colors.HexColor("#475569")
LIGHT = colors.HexColor("#F1F5F9")


def _brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _num(v, suffix=""):
    return f"{v:,.1f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_viability_pdf(data: dict) -> bytes:
    """Build viability PDF from dict.

    Expected keys: piloto_nome, municipio, propriedades (list of dicts),
    total_consumo_m3, total_economia_m3, economia_pct, biogas_m3,
    retorno_economico_brl, capex_estimado, payback_meses, adesao_pct.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Relatório de Viabilidade - AquaSuíno",
    )
    styles = getSampleStyleSheet()
    story = []

    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=EMERALD, fontSize=22, spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=DARK, fontSize=14, spaceAfter=6, spaceBefore=14)
    body = ParagraphStyle("body", parent=styles["BodyText"], textColor=DARK, fontSize=10.5, leading=15)
    muted = ParagraphStyle("muted", parent=body, textColor=GRAY, fontSize=9)

    story.append(Paragraph("AquaSuíno — Relatório de Viabilidade", h1))
    story.append(Paragraph(
        f"Piloto: <b>{data.get('piloto_nome', 'Piloto Suinocultura Sustentável')}</b> · "
        f"Município: <b>{data.get('municipio', '—')}</b> · "
        f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        muted,
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Sumário Executivo", h2))
    story.append(Paragraph(
        "Este relatório apresenta os resultados consolidados do piloto AquaSuíno para monitoramento "
        "hídrico, tratamento de dejetos e potencial de aproveitamento energético via biogás em "
        "propriedades suinícolas. Os dados abaixo refletem o modelo <b>Medir → Reduzir → Tratar → "
        "Reaproveitar</b> aplicado a uma rede-piloto de produtores integrados à Frivatti e "
        "apoiada pela Prefeitura local.",
        body,
    ))
    story.append(Spacer(1, 10))

    kpi_data = [
        ["Indicador", "Valor"],
        ["Propriedades no piloto", str(data.get("total_propriedades", 0))],
        ["Adesão do programa", f"{data.get('adesao_pct', 0):.1f}%"],
        ["Consumo total (10 meses)", _num(data.get("total_consumo_m3", 0), " m³")],
        ["Economia estimada", f"{_num(data.get('total_economia_m3', 0), ' m³')} ({data.get('economia_pct', 0):.1f}%)"],
        ["Biogás produzido", _num(data.get("biogas_m3", 0), " m³")],
        ["Retorno econômico estimado", _brl(data.get("retorno_economico_brl", 0))],
        ["CAPEX estimado (biodigestor)", _brl(data.get("capex_estimado", 0))],
        ["Payback estimado", f"{data.get('payback_meses', 0):.1f} meses"],
    ]
    tbl = Table(kpi_data, colWidths=[9 * cm, 7 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), EMERALD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)

    story.append(Paragraph("Propriedades participantes", h2))
    prop_rows = [["Propriedade", "Município", "Suínos", "Consumo m³", "Meta %", "Biodig."]]
    for p in data.get("propriedades", []):
        prop_rows.append([
            p.get("nome", "—"),
            p.get("municipio", "—"),
            str(p.get("num_suinos", 0)),
            _num(p.get("consumo_total_m3", 0)),
            f"{p.get('meta_reducao_pct', 10)}%",
            "Sim" if p.get("tem_biodigestor") else "Não",
        ])
    tbl2 = Table(prop_rows, colWidths=[4.5 * cm, 3.5 * cm, 2 * cm, 2.5 * cm, 2 * cm, 2 * cm])
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AQUA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
    ]))
    story.append(tbl2)

    story.append(PageBreak())
    story.append(Paragraph("Metodologia e premissas", h2))
    story.append(Paragraph(
        "• <b>Baseline hídrico:</b> média dos primeiros 30 dias de leitura manual por propriedade.<br/>"
        "• <b>Meta de redução:</b> 10% sobre o baseline (ajustável após 30 dias).<br/>"
        "• <b>Biogás:</b> fator técnico Embrapa Suínos e Aves — ~0,062 m³ biogás por kg de dejeto tratado.<br/>"
        "• <b>Retorno econômico:</b> soma de economia hídrica + bônus Frivatti por kg de suíno + aproveitamento energético do biogás.<br/>"
        "• <b>Licenciamento:</b> destino do digestato e reúso de água tratada em conformidade com CONAMA "
        "e Instituto Ambiental (IAT/IMA local).",
        body,
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Riscos e mitigação", h2))
    story.append(Paragraph(
        "• <b>Adesão voluntária:</b> mitigada por bônus Frivatti no kg do suíno.<br/>"
        "• <b>CAPEX do biodigestor:</b> viabilizado via Pronaf, BNDES e Programa ABC+.<br/>"
        "• <b>Biogás:</b> tratado como aproveitamento energético interno, não como venda direta.<br/>"
        "• <b>Meta de 10%:</b> apresentada como referência inicial, revisada após baseline consolidado.",
        body,
    ))
    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "Documento gerado automaticamente pela plataforma AquaSuíno. "
        "Base para estudo de viabilidade e expansão do programa.",
        muted,
    ))

    doc.build(story)
    return buf.getvalue()
