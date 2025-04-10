import oracledb
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Configura o caminho para o instant client
oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_12")
os.environ["TNS_ADMIN"] = r"C:\instantclient_21_12\network\admin"

try:
    conn = oracledb.connect(user="system", password="1234", dsn="ORACLE_TEST")
    print("[OK] Conectado com sucesso ao Oracle!")
    conn.close()
except Exception as e:
    print("[ERRO]", e)


def compilar_objetos_invalidos(user, password, tns_name, owner=None):
    oracledb.init_oracle_client(lib_dir=r"C:\instantclient_21_12")
    os.environ["TNS_ADMIN"] = r"C:\instantclient_21_12\network\admin"

    try:
        with oracledb.connect(user=user, password=password, dsn=tns_name) as conn:
            with conn.cursor() as cursor:
                filtro_owner = f" AND owner = UPPER('{owner}')" if owner else ""

                cursor.execute(f"""
                    SELECT owner, object_name, object_type
                    FROM all_objects
                    WHERE status = 'INVALID'
                    {filtro_owner}
                """)
                objetos = cursor.fetchall()

                if not objetos:
                    print("[ORACLE] Nenhum objeto inválido encontrado.")
                    return

                print(f"[ORACLE] {len(objetos)} objeto(s) inválido(s) encontrado(s). Compilando...\n")
                for owner, name, tipo in objetos:
                    tipo_compilado = tipo.replace(" BODY", "")
                    sql = f'ALTER {tipo_compilado} \"{owner}\".\"{name}\" COMPILE'
                    if "PACKAGE BODY" in tipo:
                        sql = f'ALTER PACKAGE \"{owner}\".\"{name}\" COMPILE BODY'
                    try:
                        cursor.execute(sql)
                        print(f"✔️  {sql}")
                    except Exception as e:
                        print(f"❌ Falha ao compilar {owner}.{name}: {e}")

                print("\n[ORACLE] Compilação concluída.")

    except Exception as e:
        print("[ERRO ORACLE]", e)

def listar_tabelas_oracle(user, password, tns_name):
    try:
        # Conecta usando TNS
        with oracledb.connect(user=user, password=password, dsn=tns_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT owner, table_name FROM all_tables ORDER BY owner, table_name")
                tabelas = cursor.fetchall()
                
                print(f"\n[TABELAS ENCONTRADAS: {len(tabelas)}]")
                for owner, table_name in tabelas:
                    print(f"{owner}.{table_name}")
                    
    except Exception as e:
        print(f"[ERRO AO CONSULTAR TABELAS] {e}")

def compilar_scripts_da_pasta(user, password, tns_name, pasta):

    extensoes_validas = (".sql", ".prc", ".pkb", ".pks", ".fun", ".trg", ".vw")

    try:
        with oracledb.connect(user=user, password=password, dsn=tns_name) as conn:
            with conn.cursor() as cursor:
                print(f"[INFO] Buscando scripts SQL na pasta: {pasta}")
                for root, dirs, files in os.walk(pasta):
                    for file in sorted(files):
                        if file.lower().endswith(extensoes_validas):
                            path = os.path.join(root, file)
                            print(f"[EXECUTANDO] {path}")
                            try:
                                with open(path, "r", encoding="utf-8") as f:
                                    sql = f.read()

                                # Remove o `/` do final, se existir
                                sql = sql.strip()
                                if sql.endswith("/"):
                                    sql = sql[:-1].strip()

                                cursor.execute(sql)
                                print(f"[OK] {file}")
                            except Exception as e:
                                print(f"[ERRO] Falha ao executar {file}: {e}")
    except Exception as e:
        print("[ERRO ORACLE]", e)

def run_oracle_update():
    #listar_tabelas_oracle("system", "1234", "ORACLE_TEST")
    compilar_objetos_invalidos("system", "1234", "ORACLE_TEST", owner="SYSTEM")
    compilar_scripts_da_pasta("system", "1234", "ORACLE_TEST", "alteracoes")
    compilar_objetos_invalidos("system", "1234", "ORACLE_TEST", owner="SYSTEM")


