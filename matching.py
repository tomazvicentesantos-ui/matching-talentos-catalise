import anthropic, fitz, pandas as pd, json, time
from google.colab import files

def extrair_texto_pdf(caminho):
    doc = fitz.open(caminho)
    texto = "".join(p.get_text() for p in doc)
    doc.close()
    return texto.strip()

def extrair_papeis(texto_proposta, cliente):
    prompt = f"""[prompt do Apêndice A.1]\n{texto_proposta}"""
    r = cliente.messages.create(model="claude-sonnet-4-20250514",
        max_tokens=1500, messages=[{"role":"user","content":prompt}])
    return json.loads(r.content[0].text.strip())

def avaliar_candidato(texto_cv, nome, papel, cliente):
    requisitos = "\n".join([f"- {x}" for x in papel["requisitos_chave"]])
    prompt = f"""[prompt do Apêndice A.2]"""
    for tentativa in range(3):
        try:
            r = cliente.messages.create(model="claude-sonnet-4-20250514",
                max_tokens=800, messages=[{"role":"user","content":prompt}])
            res = json.loads(r.content[0].text.strip())
            res["nome"] = nome; res["papel"] = papel["papel"]
            return res
        except Exception as e:
            if "rate_limit" in str(e).lower() and tentativa < 2:
                time.sleep(30 * (tentativa + 1))
            else:
                return {"nome":nome,"papel":papel["papel"],
                        "pontuacao":0,"adequado":False,
                        "justificativa":f"Erro: {str(e)[:80]}"}

def executar_matching():
    cliente = anthropic.Anthropic(api_key=input("API key: ").strip())
    proposta = extrair_texto_pdf(list(files.upload().keys())[0])
    papeis = extrair_papeis(proposta, cliente); time.sleep(10)
    cvs = {n.replace('.pdf','').replace('_',' ').strip():
           extrair_texto_pdf(n) for n in files.upload().keys()}
    resultados, total, i = [], len(papeis)*len(cvs), 0
    for papel in papeis:
        for nome, cv in cvs.items():
            i += 1
            print(f"[{i}/{total}] {nome} x {papel['papel']}")
            resultados.append(avaliar_candidato(cv, nome, papel, cliente))
            pd.DataFrame(resultados).to_csv("parcial.csv", index=False)
            if i < total: time.sleep(12)
    df = pd.DataFrame(resultados)
    df.to_csv("matching_final.csv", index=False, encoding="utf-8-sig")
    files.download("matching_final.csv")
    return resultados

# resultados = executar_matching()

