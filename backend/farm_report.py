"""Printable individual report with period totals and complete ledger."""
from io import BytesIO
from datetime import datetime, timezone
from collections import defaultdict
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, CondPageBreak

def build_farm_pdf(detail, inicio=None, fim=None):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42,
                            title="AquaSuíno - Relatório individual")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cell", fontSize=9, leading=12, textColor=colors.HexColor("#0f172a")))
    styles.add(ParagraphStyle(name="Muted", fontSize=9, leading=13, textColor=colors.HexColor("#475569")))
    def p(value, style="Cell"): return Paragraph(escape(str(value)), styles[style])
    def brl(cents): return (f"R$ {cents/100:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")
    def num(value): return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    def day(value): return "/".join(str(value)[:10].split("-")[::-1])
    story = []
    def table(headers, rows, widths):
        data = [[p(h) for h in headers]] + [[p(v) for v in row] for row in rows]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0),colors.HexColor("#d1fae5")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f1f5f9")]),
            ("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("TOPPADDING",(0,0),(-1,-1),8),("LINEBELOW",(0,0),(-1,0),1,colors.HexColor("#059669"))]))
        story.append(t)
    prop = detail["propriedade"]
    story += [p("AquaSuíno", "Title"), p("Relatório individual da propriedade", "Heading1"), p(prop["nome"], "Heading2")]
    story += [p(f"Responsável: {prop['produtor_nome']} | Município: {prop['municipio']}", "Muted"),
              p(f"Suínos: {prop['num_suinos']} | Área: {prop['area_m2']} m² | Hidrômetro: {prop['hidrometro_serial']}", "Muted"),
              p(f"Período: {day(inicio) if inicio else 'início do histórico'} até {day(fim) if fim else 'fim do histórico'}", "Muted"),
              p("Emitido em " + datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"), "Muted"), Spacer(1,16)]
    readings, waste, expenses = detail["leituras"], detail["dejetos"], detail["despesas"]
    total_water = sum(r.get("consumo_m3",0) for r in readings)
    total_cost = sum(r["valor_centavos"] for r in expenses)
    table(["Indicador no período", "Valor"], [
        ["Consumo de água", num(total_water) + " m³"],
        ["Despesas registradas", brl(total_cost)],
        ["Biogás estimado", num(sum(r.get("biogas_m3",0) for r in waste)) + " m³"],
        ["Meta de redução cadastrada", str(prop["meta_reducao_pct"]) + "%"],
        ["Meta por leitura (referência histórica)", num(detail["resumo"]["meta_m3"]) + " m³"],
    ], [330,180])
    story += [Spacer(1,8), p("O consumo é atribuído à data da leitura, sem rateio de intervalos. A meta usa a referência histórica da fazenda. Despesas são lançamentos reais; biogás é estimado. Ausência de registros não comprova ausência de consumo ou gastos.", "Muted")]
    months = defaultdict(lambda: [0,0])
    for r in readings: months[r["data_leitura"][:7]][0] += r.get("consumo_m3",0)
    for r in expenses: months[r["data"][:7]][1] += r["valor_centavos"]
    story += [CondPageBreak(95), p("Evolução mensal", "Heading2")]
    if months:
        table(["Mês", "Consumo (m³)", "Despesas"], [[m[5:7]+"/"+m[:4], num(v[0]), brl(v[1])] for m,v in sorted(months.items())], [120,180,210])
    else: story.append(p("Nenhum registro no período selecionado."))
    story += [CondPageBreak(95), p("Histórico de leituras", "Heading2")]
    if readings:
        table(["Data", "Hidrômetro (m³)", "Consumo (m³)"], [[day(r["data_leitura"]),num(r["leitura_m3"]),num(r.get("consumo_m3",0))] for r in readings], [120,180,210])
    else: story.append(p("Nenhuma leitura no período."))
    story += [CondPageBreak(95), p("Lançamentos de despesas", "Heading2")]
    if expenses:
        table(["Data", "Descrição", "Valor"], [[day(r["data"]),r["descricao"],brl(r["valor_centavos"])] for r in expenses], [90,310,110])
    else: story.append(p("Nenhuma despesa no período."))
    def footer(canvas, document):
        canvas.setFont("Helvetica",8); canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(42,24,"AquaSuíno | Relatório individual")
        canvas.drawRightString(A4[0]-42,24,f"Página {document.page}")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()
