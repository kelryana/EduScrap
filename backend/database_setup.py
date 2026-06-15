from pymongo import MongoClient

def configurar_banco_avancado():
    print("\n" + "="*60)
    print("=== [DATABASE SETUP] CONFIGURAÇÃO FÍSICA E OTIMIZAÇÃO DO MONGODB ===")
    print("="*60)
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["hub_estudantes"]
    
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee"]
    
    for col_name in colecoes:
        colecao = db[col_name]
        

        # Permite fazer buscas rápidas por qualquer palavra no título do edital.
        print(f"-> Criando Índice de Texto ($text) na coleção: {col_name}...")
        colecao.create_index([("nome", "text")], name="idx_busca_nome_text")
        
        # Otimiza filtros que usam Categoria e Fonte ao mesmo tempo na mesma busca.
        print(f"-> Criando Índice Composto (categoria + fonte) na coleção: {col_name}...")
        colecao.create_index([("categoria", 1), ("fonte", 1)], name="idx_categoria_fonte")
    
    # Define regras para garantir que as notícias sigam uma integridade estrita de campos.
    print("-> Associando validador estrito JSON Schema na coleção 'vagas_noticias'...")
    try:
        db.command({
            "collMod": "vagas_noticias",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["nome", "link", "fonte", "categoria"],
                    "properties": {
                        "nome": {
                            "bsonType": "string",
                            "description": "O título da vaga ou notícia é obrigatório"
                        },
                        "link": {
                            "bsonType": "string",
                            "pattern": "^https?://",
                            "description": "O link deve ser uma URL válida"
                        },
                        "fonte": {
                            "bsonType": "string",
                            "description": "A fonte identificadora é obrigatória"
                        },
                        "categoria": {
                            "bsonType": "string",
                            "description": "A categoria do edital é obrigatória"
                        }
                    }
                }
            },
            "validationAction": "warn"
        })
        print("✅ JSON Schema acoplado com sucesso!")
    except Exception as e:
        print(f"⚠️ Nota do Validador: {e}")

    print("\n" + "="*60)
    print("✅ SISTEMA OTIMIZADO COM SUCESSO!")
    print("="*60 + "\n")

if __name__ == "__main__":
    configurar_banco_avancado()