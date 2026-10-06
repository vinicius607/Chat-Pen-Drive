import base64
import hashlib
import hmac
import json
import math
import re
import secrets
import time
import uuid
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    raise SystemExit("Falta a biblioteca de criptografia. Instale com:\n    pip install cryptography")


APP_DIR = Path.home() / ".chat_pendrive"
USUARIOS_FILE = APP_DIR / "usuarios.json"
CONFIG_FILE = APP_DIR / "config.json"
PASTA_NO_PENDRIVE = "chat_pendrive"  
SALT_CHAT = b"chat_pendrive_v1"       

APP_DIR.mkdir(parents=True, exist_ok=True)



def ler_json(caminho: Path, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return padrao


def gravar_json(caminho: Path, dados) -> None:
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    tmp.replace(caminho)



def gerar_hash(senha: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 200_000).hex()


def nome_valido(nome: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_.-]{3,20}", nome) is not None


def cadastrar_usuario(nome: str, senha: str) -> str | None:
    if not nome_valido(nome):
        return "Usuário: 3 a 20 caracteres (letras, números, _ . -)."
    if len(senha) < 4:
        return "A senha precisa ter pelo menos 4 caracteres."
    usuarios = ler_json(USUARIOS_FILE, {})
    if nome.lower() in (u.lower() for u in usuarios):
        return "Esse usuário já existe."
    salt = secrets.token_bytes(16)
    usuarios[nome] = {"salt": salt.hex(), "hash": gerar_hash(senha, salt)}
    gravar_json(USUARIOS_FILE, usuarios)
    return None


def autenticar(nome: str, senha: str) -> bool:
    usuarios = ler_json(USUARIOS_FILE, {})
    dados = usuarios.get(nome)
    if not dados:
        return False
    hash_calculado = gerar_hash(senha, bytes.fromhex(dados["salt"]))
    return hmac.compare_digest(hash_calculado, dados["hash"])


def montar_arvore(n: int) -> tuple[list[int], list[int], int]:
    esq = [-1] * n
    dire = [-1] * n

    def montar(inicio: int, fim: int) -> int:
        if inicio > fim:
            return -1
        meio = (inicio + fim + 1) // 2
        esq[meio] = montar(inicio, meio - 1)
        dire[meio] = montar(meio + 1, fim)
        return meio

    return esq, dire, montar(0, n - 1)


def ordem_pos_ordem(n: int) -> list[int]:
    esq, dire, raiz = montar_arvore(n)
    resultado: list[int] = []

    def visitar(i: int) -> None:
        if i < 0:
            return
        visitar(esq[i])      
        visitar(dire[i])     
        resultado.append(i)  

    visitar(raiz)
    return resultado


def cifrar_arvore(texto: str) -> str:
    ordem = ordem_pos_ordem(len(texto))
    return "".join(texto[i] for i in ordem)


def decifrar_arvore(cifrado: str) -> str:
    ordem = ordem_pos_ordem(len(cifrado))
    original = [""] * len(cifrado)
    for k, posicao in enumerate(ordem):
        original[posicao] = cifrado[k]
    return "".join(original)



def criar_fernet(chave_chat: str) -> Fernet:
    chave = hashlib.pbkdf2_hmac("sha256", chave_chat.encode("utf-8"), SALT_CHAT, 390_000, dklen=32)
    return Fernet(base64.urlsafe_b64encode(chave))


def criptografar(fernet: Fernet, mensagem: dict) -> bytes:
    return fernet.encrypt(json.dumps(mensagem, ensure_ascii=False).encode("utf-8"))


def descriptografar(fernet: Fernet, conteudo: bytes) -> dict | None:
    try:
        dados = json.loads(fernet.decrypt(conteudo).decode("utf-8"))
    except (InvalidToken, ValueError):
        return None
    return dados if isinstance(dados, dict) else None



def arquivo_historico(usuario: str) -> Path:
    return APP_DIR / f"historico_{usuario}.json"


def carregar_historico(usuario: str) -> list:
    return ler_json(arquivo_historico(usuario), [])


def salvar_historico(usuario: str, historico: list) -> None:
    gravar_json(arquivo_historico(usuario), historico)


BG = "#f8f9fb"
BRANCO = "#ffffff"
BORDA = "#e2e5ea"
TEXTO = "#111827"
CINZA = "#6b7280"
AZUL = "#2563eb"
AZUL_HOVER = "#1d4ed8"
DESAB_BG = "#f0f1f3"
DESAB_FG = "#9ca3af"
VERDE = "#15803d"
VERMELHO = "#b91c1c"
FONTE = "Segoe UI"
FONTE_MONO = "Consolas"
LIMITE_DESENHO = 1000


def altura_arvore(n: int) -> int:
    return n.bit_length()


def letra(c: str) -> str:
    return {" ": "·", "\n": "↵", "\t": "→"}.get(c, c)


class Botao(tk.Label):

    def __init__(self, pai, texto, comando, primario=True, **opcoes):
        super().__init__(pai, text=texto, font=(FONTE, 11, "bold"), pady=9, padx=12, **opcoes)
        self.comando = comando
        self.primario = primario
        self.ativo = True
        self.bind("<Button-1>", self._clique)
        self.bind("<Enter>", lambda e: self._pintar(True))
        self.bind("<Leave>", lambda e: self._pintar(False))
        self._pintar(False)

    def _pintar(self, sobre: bool):
        if not self.ativo:
            bg, fg, cursor = DESAB_BG, DESAB_FG, "arrow"
        elif self.primario:
            bg, fg, cursor = (AZUL_HOVER if sobre else AZUL), "white", "hand2"
        else:
            bg, fg, cursor = (DESAB_BG if sobre else BRANCO), TEXTO, "hand2"
        self.config(bg=bg, fg=fg, cursor=cursor)

    def _clique(self, _evento):
        if self.ativo:
            self.comando()

    def definir_ativo(self, ativo: bool):
        self.ativo = ativo
        self._pintar(False)


def criar_card(pai, titulo: str):
    externo = tk.Frame(pai, bg=BRANCO, highlightbackground=BORDA, highlightthickness=1)
    tk.Label(externo, text=titulo, bg=BRANCO, fg=TEXTO, font=(FONTE, 11, "bold"),
             anchor="w", padx=20, pady=12).pack(fill="x")
    tk.Frame(externo, bg=BORDA, height=1).pack(fill="x", padx=20)
    corpo = tk.Frame(externo, bg=BRANCO, padx=20, pady=16)
    corpo.pack(fill="both", expand=True)
    return externo, corpo


def criar_area_texto(pai, somente_leitura: bool = False, altura: int | None = None):
    container = tk.Frame(pai, bg=BRANCO, highlightbackground=BORDA, highlightthickness=1)
    barra = tk.Scrollbar(container)
    barra.pack(side="right", fill="y")
    opcoes = {"height": altura} if altura else {}
    texto = tk.Text(container, wrap="word", relief="flat", bd=0, highlightthickness=0,
                    font=(FONTE_MONO, 11), padx=12, pady=10, bg=BRANCO, fg=TEXTO,
                    insertbackground=TEXTO, yscrollcommand=barra.set, **opcoes)
    texto.pack(side="left", fill="both", expand=True)
    barra.config(command=texto.yview)
    if somente_leitura:
        texto.config(state="disabled")
    return container, texto


def criar_campo(pai, rotulo: str, oculto: bool = False) -> tk.Entry:
    tk.Label(pai, text=rotulo, bg=BRANCO, fg=CINZA, font=(FONTE, 10), anchor="w").pack(fill="x", pady=(10, 3))
    campo = tk.Entry(pai, width=36, show="*" if oculto else "", relief="flat", font=(FONTE, 11),
                     highlightthickness=1, highlightbackground=BORDA, highlightcolor=AZUL)
    campo.pack(fill="x", ipady=6)
    return campo


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chat por Pendrive")
        self.geometry("1000x780")
        self.minsize(900, 700)
        self.configure(bg=BG)

        self.usuario: str | None = None
        self.historico: list = []
        self.fernet: Fernet | None = None
        self.pasta_pendrive: str = ler_json(CONFIG_FILE, {}).get("pasta_pendrive", "")
        self.frame: tk.Frame | None = None

  
        self.texto_gerado: str | None = None   
        self.pendente: dict | None = None      

        self.tela_login()


    def trocar_frame(self) -> tk.Frame:
        if self.frame is not None:
            self.frame.destroy()
        self.frame = tk.Frame(self, bg=BG)
        self.frame.pack(fill="both", expand=True)
        return self.frame

    @staticmethod
    def definir_status(rotulo: tk.Label, texto: str, cor: str = CINZA):
        rotulo.config(text=texto, fg=cor)


    def tela_login(self):
        f = self.trocar_frame()
        card = tk.Frame(f, bg=BRANCO, highlightbackground=BORDA, highlightthickness=1, padx=40, pady=30)
        card.place(relx=0.5, rely=0.46, anchor="center")

        tk.Label(card, text="Chat por Pendrive", bg=BRANCO, fg=TEXTO,
                 font=(FONTE, 18, "bold")).pack(pady=(0, 8))
        tk.Label(card, text="Entre com seu usuário ou cadastre-se", bg=BRANCO, fg=CINZA,
                 font=(FONTE, 10)).pack()

        self.ent_usuario = criar_campo(card, "Usuário")
        self.ent_senha = criar_campo(card, "Senha", oculto=True)
        self.ent_chave = criar_campo(card, "Chave secreta do chat (igual nos dois computadores)", oculto=True)

        Botao(card, "Entrar", self.fazer_login).pack(fill="x", pady=(22, 8))
        Botao(card, "Cadastrar", self.fazer_cadastro, primario=False,
              highlightthickness=1, highlightbackground=BORDA).pack(fill="x")

        self.ent_usuario.focus()
        self.ent_usuario.bind("<Return>", lambda e: self.ent_senha.focus())
        self.ent_senha.bind("<Return>", lambda e: self.ent_chave.focus())
        self.ent_chave.bind("<Return>", lambda e: self.fazer_login())

    def fazer_login(self):
        nome = self.ent_usuario.get().strip()
        senha = self.ent_senha.get()
        chave_chat = self.ent_chave.get()
        if len(chave_chat) < 4:
            messagebox.showwarning("Chave do chat", "Digite a chave secreta do chat (mínimo 4 caracteres).")
            return
        if autenticar(nome, senha):
            self.fernet = criar_fernet(chave_chat)
            self.usuario = nome
            self.historico = carregar_historico(nome)
            self.tela_principal()
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.")
            self.ent_senha.delete(0, "end")

    def fazer_cadastro(self):
        erro = cadastrar_usuario(self.ent_usuario.get().strip(), self.ent_senha.get())
        if erro:
            messagebox.showwarning("Cadastro", erro)
        else:
            messagebox.showinfo("Cadastro", "Usuário criado! Agora clique em Entrar.")


    def tela_principal(self):
        f = self.trocar_frame()
        self.texto_gerado = None
        self.pendente = None

        topo = tk.Frame(f, bg=BRANCO)
        topo.pack(fill="x")
        self.abas: dict[str, tk.Label] = {}
        for i, nome in enumerate(("Escrever", "Ler")):
            aba = tk.Label(topo, text=nome, bg=BRANCO, font=(FONTE, 11, "bold"), padx=14, pady=18,
                           cursor="hand2", highlightthickness=1, highlightbackground=BRANCO)
            aba.pack(side="left", padx=(40 if i == 0 else 10, 0))
            aba.bind("<Button-1>", lambda e, n=nome: self.mostrar_aba(n))
            self.abas[nome] = aba


        direita = tk.Frame(topo, bg=BRANCO)
        direita.pack(side="right", padx=30)
        sair = tk.Label(direita, text="Sair", bg=BRANCO, fg=CINZA, cursor="hand2", font=(FONTE, 10, "underline"))
        sair.pack(side="right", padx=(14, 0))
        sair.bind("<Button-1>", lambda e: self.sair())
        escolher = tk.Label(direita, text="Escolher pen drive", bg=BRANCO, fg=AZUL, cursor="hand2",
                            font=(FONTE, 10, "underline"))
        escolher.pack(side="right", padx=(14, 0))
        escolher.bind("<Button-1>", lambda e: self.escolher_pendrive())
        self.lbl_pendrive = tk.Label(direita, bg=BRANCO, fg=CINZA, font=(FONTE, 10))
        self.lbl_pendrive.pack(side="right")
        tk.Label(direita, text=f"Usuário: {self.usuario}   |", bg=BRANCO, fg=TEXTO,
                 font=(FONTE, 10, "bold")).pack(side="right", padx=(0, 10))
        self.atualizar_label_pendrive()

        tk.Frame(f, bg=BORDA, height=1).pack(fill="x")

        corpo = tk.Frame(f, bg=BG, padx=40, pady=24)
        corpo.pack(fill="both", expand=True)
        self.pagina_escrever = self.montar_pagina_escrever(corpo)
        self.pagina_ler = self.montar_pagina_ler(corpo)
        self.mostrar_aba("Escrever")

    def mostrar_aba(self, nome: str):
        for n, aba in self.abas.items():
            selecionada = n == nome
            aba.config(fg=AZUL if selecionada else CINZA,
                       highlightbackground=AZUL if selecionada else BRANCO)
        self.pagina_escrever.pack_forget()
        self.pagina_ler.pack_forget()
        pagina = self.pagina_escrever if nome == "Escrever" else self.pagina_ler
        pagina.pack(fill="both", expand=True)
        if nome == "Ler":
            self.mostrar_historico()

    def atualizar_label_pendrive(self):
        self.lbl_pendrive.config(
            text=f"Pen drive: {self.pasta_pendrive}" if self.pasta_pendrive else "Pen drive: nenhum selecionado")


    def montar_pagina_escrever(self, pai) -> tk.Frame:
        pag = tk.Frame(pai, bg=BG)
        tk.Label(pag, text="Escrever", font=(FONTE, 20, "bold"), bg=BG, fg=TEXTO,
                 anchor="w").pack(fill="x", pady=(0, 14))

        colunas = tk.Frame(pag, bg=BG)
        colunas.pack(fill="both", expand=True)
        colunas.columnconfigure(0, weight=3)
        colunas.columnconfigure(1, weight=1, minsize=300)
        colunas.rowconfigure(0, weight=1)
        esquerda = tk.Frame(colunas, bg=BG)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 24))
        direita = tk.Frame(colunas, bg=BG)
        direita.grid(row=0, column=1, sticky="new")


        self.card_editor, corpo_editor = criar_card(esquerda, "Editor de Texto")
        self.card_editor.pack(fill="both", expand=True)
        container, self.editor = criar_area_texto(corpo_editor, altura=10)
        container.pack(fill="both", expand=True)
        self.editor.bind("<KeyRelease>", self.ao_editar)


        self.card_resultado, corpo_res = criar_card(esquerda, "Mensagem criptografada")
        topo_res = tk.Frame(corpo_res, bg=BRANCO)
        topo_res.pack(fill="x", pady=(0, 8))
        Botao(topo_res, "Ver desenho da árvore", lambda: self.desenhar_arvore(
            self.pendente["texto"], "pos") if self.pendente else None, primario=False,
            highlightthickness=1, highlightbackground=BORDA).pack(side="left")
        container_res, self.txt_resultado = criar_area_texto(corpo_res, somente_leitura=True, altura=9)
        container_res.pack(fill="x")
        self.txt_resultado.tag_config("titulo", font=(FONTE, 10, "bold"), foreground=CINZA)

        # Painel de Controle
        card_ctrl, corpo_ctrl = criar_card(direita, "Painel de Controle")
        card_ctrl.pack(fill="x")
        self.btn_gerar = Botao(corpo_ctrl, "Gerar árvore", self.gerar_arvore)
        self.btn_gerar.pack(fill="x", pady=(0, 10))
        self.btn_cripto = Botao(corpo_ctrl, "Criptografar árvore", self.criptografar_arvore)
        self.btn_cripto.pack(fill="x", pady=(0, 10))
        self.btn_salvar = Botao(corpo_ctrl, "Salvar no Pen Drive", self.salvar_pendrive)
        self.btn_salvar.pack(fill="x")
        self.btn_cripto.definir_ativo(False)
        self.btn_salvar.definir_ativo(False)
        self.lbl_status_escrever = tk.Label(corpo_ctrl, text="", bg=BRANCO, fg=CINZA, wraplength=260,
                                            justify="left", anchor="w", font=(FONTE, 10))
        self.lbl_status_escrever.pack(fill="x", pady=(14, 0))
        return pag

    def texto_do_editor(self) -> str:
        return self.editor.get("1.0", "end-1c").strip()

    def invalidar(self):
        self.texto_gerado = None
        self.pendente = None
        self.btn_cripto.definir_ativo(False)
        self.btn_salvar.definir_ativo(False)
        self.card_resultado.pack_forget()

    def ao_editar(self, _evento=None):
        if self.texto_gerado is not None and self.texto_do_editor() != self.texto_gerado:
            self.invalidar()
            self.definir_status(self.lbl_status_escrever, "Texto alterado: gere a árvore novamente.")

    def gerar_arvore(self):
        texto = self.texto_do_editor()
        if not texto:
            self.definir_status(self.lbl_status_escrever, "Digite uma mensagem no editor.", VERMELHO)
            return
        self.invalidar()
        self.texto_gerado = texto
        n = len(texto)
        aviso = f"Árvore gerada: {n} nós, altura {altura_arvore(n)}. Agora criptografe a árvore."
        if n > LIMITE_DESENHO:
            aviso += f" (O desenho só é exibido até {LIMITE_DESENHO} letras.)"
        self.btn_cripto.definir_ativo(True)
        self.definir_status(self.lbl_status_escrever, aviso, VERDE)
        if n <= LIMITE_DESENHO:
            self.desenhar_arvore(texto, "em")

    def criptografar_arvore(self):
        if self.texto_gerado is None:
            return
        texto = self.texto_gerado
        agora = time.time()
        mensagem = {
            "id": uuid.uuid4().hex,
            "de": self.usuario,
            "texto": cifrar_arvore(texto),
            "ts": agora,
            "data": datetime.fromtimestamp(agora).strftime("%d/%m/%Y %H:%M"),
        }
        token = criptografar(self.fernet, mensagem)
        self.pendente = {"mensagem": mensagem, "token": token, "texto": texto}

        self.txt_resultado.config(state="normal")
        self.txt_resultado.delete("1.0", "end")
        for titulo, conteudo in (
            ("Mensagem original", texto),
            ("1) Depois da árvore (percurso pós-ordem)", mensagem["texto"]),
            ("2) Depois do AES", token.decode("ascii")),
        ):
            self.txt_resultado.insert("end", titulo + "\n", "titulo")
            self.txt_resultado.insert("end", conteudo + "\n\n")
        self.txt_resultado.config(state="disabled")
        self.card_editor.pack_forget()
        self.card_resultado.pack(side="bottom", fill="x", pady=(16, 0))
        self.card_editor.pack(fill="both", expand=True)

        self.btn_salvar.definir_ativo(True)
        self.definir_status(self.lbl_status_escrever,
                            "Árvore criptografada. Clique em Salvar no Pen Drive.", VERDE)

    def salvar_pendrive(self):
        if self.pendente is None:
            return
        pasta = self.pasta_de_mensagens(criar=True)
        if pasta is None:
            return
        mensagem = self.pendente["mensagem"]
        destino = pasta / f"{mensagem['id']}.enc"
        try:
            tmp = destino.with_suffix(".tmp")
            tmp.write_bytes(self.pendente["token"])
            tmp.replace(destino)
        except OSError as e:
            messagebox.showerror("Erro ao gravar", f"Não consegui gravar no pen drive:\n{e}")
            return

        self.historico.append({
            "id": mensagem["id"], "tipo": "enviada", "de": self.usuario,
            "texto": self.pendente["texto"], "ts": mensagem["ts"], "data": mensagem["data"],
        })
        salvar_historico(self.usuario, self.historico)
        self.editor.delete("1.0", "end")
        self.invalidar()
        self.definir_status(self.lbl_status_escrever, "Mensagem salva no pen drive.", VERDE)
        self.mostrar_historico()


    def montar_pagina_ler(self, pai) -> tk.Frame:
        pag = tk.Frame(pai, bg=BG)
        tk.Label(pag, text="Ler", font=(FONTE, 20, "bold"), bg=BG, fg=TEXTO,
                 anchor="w").pack(fill="x", pady=(0, 14))

        colunas = tk.Frame(pag, bg=BG)
        colunas.pack(fill="both", expand=True)
        colunas.columnconfigure(0, weight=3)
        colunas.columnconfigure(1, weight=1, minsize=300)
        colunas.rowconfigure(0, weight=1)
        esquerda = tk.Frame(colunas, bg=BG)
        esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 24))
        direita = tk.Frame(colunas, bg=BG)
        direita.grid(row=0, column=1, sticky="new")

        card_hist, corpo_hist = criar_card(esquerda, "Histórico de mensagens")
        card_hist.pack(fill="both", expand=True)
        container, self.txt_historico = criar_area_texto(corpo_hist, somente_leitura=True)
        container.pack(fill="both", expand=True)
        self.txt_historico.tag_config("enviada", foreground="#1a5fb4", font=(FONTE, 10, "bold"))
        self.txt_historico.tag_config("recebida", foreground=VERDE, font=(FONTE, 10, "bold"))
        self.txt_historico.tag_config("vazio", foreground=CINZA, font=(FONTE, 10, "italic"))

        card_ctrl, corpo_ctrl = criar_card(direita, "Painel de Controle")
        card_ctrl.pack(fill="x")
        Botao(corpo_ctrl, "Ler do Pen Drive", self.ler).pack(fill="x")
        self.lbl_status_ler = tk.Label(corpo_ctrl, text="", bg=BRANCO, fg=CINZA, wraplength=260,
                                       justify="left", anchor="w", font=(FONTE, 10))
        self.lbl_status_ler.pack(fill="x", pady=(14, 0))
        return pag

    def mostrar_historico(self):
        t = self.txt_historico
        t.config(state="normal")
        t.delete("1.0", "end")
        if not self.historico:
            t.insert("end", "Nenhuma mensagem ainda.\n", "vazio")
        for m in self.historico:
            if m["tipo"] == "enviada":
                t.insert("end", f"[{m['data']}] Mensagem enviada\n", "enviada")
            else:
                t.insert("end", f"[{m['data']}] {m['de']}\n", "recebida")
            t.insert("end", m["texto"] + "\n\n")
        t.config(state="disabled")
        t.see("end")

    def ler(self):
        pasta = self.pasta_de_mensagens(criar=False)
        if pasta is None:
            return
        if not pasta.exists():
            self.definir_status(self.lbl_status_ler, "Nenhuma mensagem encontrada neste pen drive.")
            return

        ids_conhecidos = {m["id"] for m in self.historico}
        novas = []
        falhas = 0
        for arq in pasta.glob("*.enc"):
            if arq.stem in ids_conhecidos:
                continue  
            try:
                conteudo = arq.read_bytes()
            except OSError:
                continue
            dados = descriptografar(self.fernet, conteudo)
            if dados is None or not all(k in dados for k in ("id", "de", "texto", "ts", "data")):
                falhas += 1
                continue
            if dados["de"] == self.usuario or dados["id"] in ids_conhecidos:
                continue
            dados["texto"] = decifrar_arvore(dados["texto"])  
            novas.append(dados)

        novas.sort(key=lambda m: m["ts"])
        for m in novas:
            self.historico.append({
                "id": m["id"], "tipo": "recebida", "de": m["de"],
                "texto": m["texto"], "ts": m["ts"], "data": m["data"],
            })
        if novas:
            salvar_historico(self.usuario, self.historico)
            self.mostrar_historico()

        partes = []
        if novas:
            partes.append(f"{len(novas)} mensagem(ns) nova(s) adicionada(s) ao histórico.")
        else:
            partes.append("Nenhuma mensagem nova.")
        if falhas:
            partes.append(f"{falhas} arquivo(s) não puderam ser lidos: chave secreta diferente?")
        self.definir_status(self.lbl_status_ler, " ".join(partes), VERMELHO if falhas else (VERDE if novas else CINZA))


    def escolher_pendrive(self) -> bool:
        pasta = filedialog.askdirectory(title="Selecione o pen drive (ou uma pasta dele)")
        if not pasta:
            return False
        self.pasta_pendrive = pasta
        config = ler_json(CONFIG_FILE, {})
        config["pasta_pendrive"] = pasta
        gravar_json(CONFIG_FILE, config)
        self.atualizar_label_pendrive()
        return True

    def pasta_de_mensagens(self, criar: bool) -> Path | None:
        if not self.pasta_pendrive:
            if not self.escolher_pendrive():
                return None
        base = Path(self.pasta_pendrive)
        if not base.exists():
            messagebox.showerror("Pen drive", "Não encontrei o pen drive. Ele está conectado?")
            return None
        pasta = base / PASTA_NO_PENDRIVE
        if criar:
            pasta.mkdir(exist_ok=True)
        return pasta


    def desenhar_arvore(self, texto: str, percurso_inicial: str = "em"):
        n = len(texto)
        if n == 0:
            return
        if n > LIMITE_DESENHO:
            messagebox.showinfo("Desenho", f"Mensagem longa demais para desenhar (máximo {LIMITE_DESENHO} letras).")
            return

        esq, dire, raiz = montar_arvore(n)
        profundidade: dict[int, int] = {}

        def medir(i: int, d: int):
            if i < 0:
                return
            profundidade[i] = d
            medir(esq[i], d + 1)
            medir(dire[i], d + 1)

        medir(raiz, 0)

        dx, dy, r = 44, 62, 17          
        cw, ch = 40, 34                  
        azul = "#3f3fd0"
        niveis = max(profundidade.values()) + 1
        y_vetor = 50 + niveis * dy
        largura = max(70 + n * dx, 50 + n * cw, 560)
        altura = y_vetor + ch + 40

        def centro(i: int):
            return 40 + i * dx, 40 + profundidade[i] * dy

        janela = tk.Toplevel(self)
        janela.title("Árvore binária")
        janela.geometry(f"{min(largura + 40, 1000)}x{min(altura + 110, 720)}")
        janela.configure(bg=BG)

        topo = tk.Frame(janela, bg=BG)
        topo.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(topo, text="Percurso ", font=(FONTE, 15, "bold"), bg=BG, fg=TEXTO).pack(side="left")
        lbl_nome = tk.Label(topo, font=(FONTE, 15, "bold"), fg=azul, bg=BG)
        lbl_nome.pack(side="left")

        area = tk.Frame(janela, bg=BG)
        area.pack(fill="both", expand=True, padx=12, pady=10)
        canvas = tk.Canvas(area, bg="white", highlightthickness=1, highlightbackground="#bbbbbb",
                           scrollregion=(0, 0, largura, altura))
        barra = tk.Scrollbar(area, orient="horizontal", command=canvas.xview)
        canvas.config(xscrollcommand=barra.set)
        barra.pack(side="bottom", fill="x")
        canvas.pack(side="top", fill="both", expand=True)

        def desenhar(percurso: str):
            canvas.delete("all")
            if percurso == "em":
                sequencia = list(range(n))
                lbl_nome.config(text="Em Ordem (mensagem original)")
            else:
                sequencia = ordem_pos_ordem(n)
                lbl_nome.config(text="Pós-Ordem (mensagem cifrada)")
            ordem_de = {pos: k + 1 for k, pos in enumerate(sequencia)}

            for i in profundidade:
                for filho in (esq[i], dire[i]):
                    if filho >= 0:
                        x1, y1 = centro(i)
                        x2, y2 = centro(filho)
                        canvas.create_line(x1, y1, x2, y2, fill="#444444", width=2)

            for a, b in zip(sequencia, sequencia[1:]):
                x1, y1 = centro(a)
                x2, y2 = centro(b)
                dist = math.hypot(x2 - x1, y2 - y1)
                ux, uy = (x2 - x1) / dist, (y2 - y1) / dist
                nx, ny = -uy, ux
                curva = min(30, 10 + dist * 0.15)
                cx, cy = (x1 + x2) / 2 + nx * curva, (y1 + y2) / 2 + ny * curva
                canvas.create_line(x1 + ux * r, y1 + uy * r, cx, cy, x2 - ux * r, y2 - uy * r,
                                   smooth=True, arrow="last", arrowshape=(10, 12, 4),
                                   fill=azul, width=2)

            for i in profundidade:
                x, y = centro(i)
                canvas.create_oval(x - r, y - r, x + r, y + r, fill="#cfe0ff", outline="#222222", width=2)
                canvas.create_text(x, y, text=letra(texto[i]), font=(FONTE_MONO, 12, "bold"))
                canvas.create_text(x - r - 2, y - r - 4, text=f"{ordem_de[i]}º", fill=azul,
                                   font=(FONTE, 10, "bold"))

            for k, i in enumerate(sequencia):
                x = 20 + k * cw
                canvas.create_text(x + cw / 2, y_vetor - 10, text=str(k + 1), font=(FONTE, 9))
                canvas.create_rectangle(x, y_vetor, x + cw, y_vetor + ch, outline="black", width=1)
                canvas.create_text(x + cw / 2, y_vetor + ch / 2, text=letra(texto[i]),
                                   font=(FONTE_MONO, 14, "bold"))

        tk.Button(topo, text="Pós-ordem (cifrado)", command=lambda: desenhar("pos")).pack(side="right")
        tk.Button(topo, text="Em ordem (original)", command=lambda: desenhar("em")).pack(side="right", padx=5)
        desenhar(percurso_inicial)

    # ------------------------------------------------------------------
    def sair(self):
        self.usuario = None
        self.historico = []
        self.fernet = None
        self.texto_gerado = None
        self.pendente = None
        self.tela_login()


if __name__ == "__main__":
    App().mainloop()