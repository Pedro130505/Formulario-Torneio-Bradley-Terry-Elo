import sqlite3

# Mapeamento com fotos profissionais de alta qualidade para brindes corporativos
IMAGENS_BRINDES = {
    # Itens de Escrita e Papelaria
    "Caneta": "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=600&auto=format&fit=crop&q=80",
    "Caderno Grande": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",
    "Caderno de Bolso": "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=600&auto=format&fit=crop&q=80",
    "Bloco de Notas": "https://images.unsplash.com/photo-1517842645767-c639042777db?w=600&auto=format&fit=crop&q=80",
    "Lápis": "https://images.unsplash.com/photo-1585336261026-7f5b49747867?w=600&auto=format&fit=crop&q=80",
    "Caderno de papel semente": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=600&auto=format&fit=crop&q=80",
    "Lápis biodegradável": "https://images.unsplash.com/photo-1569683795645-b62e50fbf103?w=600&auto=format&fit=crop&q=80",
    "Cadernos de cortiça ou papelão kraft": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",
    "Cadernos executivos tipo Moleskine": "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=600&auto=format&fit=crop&q=80",
    "Planners não datados": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=600&auto=format&fit=crop&q=80",
    "Blocos de anotação reutilizáveis": "https://images.unsplash.com/photo-1517842645767-c639042777db?w=600&auto=format&fit=crop&q=80",
    "Marca página magnético personalizado": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",

    # Bebidas, Garrafas e Copos
    "Copo": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80",
    "Garrafa": "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=600&auto=format&fit=crop&q=80",
    "Canudos de inox": "https://images.unsplash.com/photo-1616401784845-180882ba9ba8?w=600&auto=format&fit=crop&q=80",
    "Garrafas e copos térmicos a vácuo": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&auto=format&fit=crop&q=80",
    "Garrafas de silicone retráteis": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&auto=format&fit=crop&q=80",
    "Squeezes com marcação de horários": "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=600&auto=format&fit=crop&q=80",
    "Copo térmico personalizado": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=600&auto=format&fit=crop&q=80",
    "Kit relacionado a café": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&auto=format&fit=crop&q=80",

    # Tecnologia e Gadgets
    "Power banks": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=600&auto=format&fit=crop&q=80",
    "Carregadores portáteis por indução": "https://images.unsplash.com/photo-1622445262464-84b14e3295b6?w=600&auto=format&fit=crop&q=80",
    "Cabos de carregamento 3 em 1": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=80",
    "Hubs USB": "https://images.unsplash.com/photo-1622445262464-84b14e3295b6?w=600&auto=format&fit=crop&q=80",
    "Tampas de segurança para webcam": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop&q=80",
    "Ring lights de presilha": "https://images.unsplash.com/photo-1616469829941-c7200edec809?w=600&auto=format&fit=crop&q=80",
    "Luminárias LED": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&auto=format&fit=crop&q=80",
    "Tags rastreadoras bluetooth": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
    "Fones de ouvido": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
    "Caixas de som": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600&auto=format&fit=crop&q=80",
    "Kindle": "https://images.unsplash.com/photo-1592496001020-d31bd830651f?w=600&auto=format&fit=crop&q=80",
    "Mesa digitalizadora": "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600&auto=format&fit=crop&q=80",
    "Adesivo NFC em Botton": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80",

    # Bolsas, Mochilas e Acessórios
    "Ecobags de lona ou algodão cru": "https://images.unsplash.com/photo-1597484661643-2f5fef640dd1?w=600&auto=format&fit=crop&q=80",
    "Sacochilas de nylon": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
    "Sacolas retornáveis": "https://images.unsplash.com/photo-1597484661643-2f5fef640dd1?w=600&auto=format&fit=crop&q=80",
    "Mochilas executivas": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
    "Shoulder bag": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600&auto=format&fit=crop&q=80",
    "Estojos e nécessaires": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=600&auto=format&fit=crop&q=80",
    "Capa para notebook personalizada": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=600&auto=format&fit=crop&q=80",
    "Dead Hat (boné personalizado)": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=600&auto=format&fit=crop&q=80",
    "Corta-vento institucional": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=600&auto=format&fit=crop&q=80",
    "Blusa de time": "https://images.unsplash.com/photo-1577210897949-1f56f9435827?w=600&auto=format&fit=crop&q=80",
    "Capas de chuva portáteis": "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?w=600&auto=format&fit=crop&q=80",

    # Escritório, Mesa e Organização
    "Mousepads": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop&q=80",
    "Suportes para notebook ou celular": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format&fit=crop&q=80",
    "Organizadores de mesa modulares": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&auto=format&fit=crop&q=80",
    "Clipes organizadores magnéticos": "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=600&auto=format&fit=crop&q=80",
    "Organizadores de cabos": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=80",
    "Limpadores de tela spray": "https://images.unsplash.com/photo-1584744982491-665216d95f8b?w=600&auto=format&fit=crop&q=80",

    # Crachás, Cartões e Identificação
    "Cordões para crachá": "https://images.unsplash.com/photo-1614252369475-531eba835eb1?w=600&auto=format&fit=crop&q=80",
    "Porta-cartões ou porta-crachá": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80",
    "Porta cartão adesivo para celular": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80",
    "Carteira de cartão": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&auto=format&fit=crop&q=80",
    "Credencial PVC": "https://images.unsplash.com/photo-1614252369475-531eba835eb1?w=600&auto=format&fit=crop&q=80",
    "Bottons e pins esmaltados": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80",
    "Chaveiro de metal personalizado": "https://images.unsplash.com/photo-1614252369475-531eba835eb1?w=600&auto=format&fit=crop&q=80",
    "Chaveiro botton": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80",

    # Bem-Estar e Cuidados
    "Bolinha anti-estresse": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&auto=format&fit=crop&q=80",
    "Bolinhas de massagem": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&auto=format&fit=crop&q=80",
    "Almofadas lombares": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=600&auto=format&fit=crop&q=80",
    "Máscaras de dormir": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80",
    "Mini ventilador portátil": "https://images.unsplash.com/photo-1618941716939-553df3c6c278?w=600&auto=format&fit=crop&q=80",
    "Álcool em gel com capa personalizada": "https://images.unsplash.com/photo-1584744982491-665216d95f8b?w=600&auto=format&fit=crop&q=80",
    "Protetor labial": "https://images.unsplash.com/photo-1599305090598-fe179d501227?w=600&auto=format&fit=crop&q=80",

    # Outros
    "Ferramentas": "https://images.unsplash.com/photo-1581783342308-f792dbdd27c5?w=600&auto=format&fit=crop&q=80",
    "Ingresso para shows/jogos": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=600&auto=format&fit=crop&q=80"
}

# Imagem padrão para qualquer brinde
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=600&auto=format&fit=crop&q=80"

conn = sqlite3.connect("torneio.db")
cursor = conn.cursor()

itens = cursor.execute("SELECT id, nome FROM itens").fetchall()
atualizados = 0

for item_id, nome in itens:
    # Busca imagem exata ou correspondente
    img_url = IMAGENS_BRINDES.get(nome)
    if not img_url:
        for k, v in IMAGENS_BRINDES.items():
            if k.lower() in nome.lower() or nome.lower() in k.lower():
                img_url = v
                break
    if not img_url:
        img_url = DEFAULT_IMAGE

    cursor.execute("UPDATE itens SET imagem_url = ? WHERE id = ?", (img_url, item_id))
    atualizados += 1

conn.commit()
print(f"Sucesso! {atualizados} itens atualizados com fotos de alta qualidade.")
