import sys
import bcrypt

from PyQt6 import QtWidgets, uic

from src.dashboard import TelaDashboard
from src.cadastro import TelaCadastro
from utils.cnn import conectar

class TelaLogin(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        # Carrega a interface
        uic.loadUi("views/login.ui", self)

        # Oculta a senha
        self.txt_senha.setEchoMode(
            QtWidgets.QLineEdit.EchoMode.Password
        )

        # Eventos
        self.btn_entrar.clicked.connect(
            self.verificar_login
        )

        self.btn_cadastro.clicked.connect(
            self.tela_cadastro
        )

        # Permite efetuar login pressionando Enter
        self.txt_senha.returnPressed.connect(
            self.verificar_login
        )

    def tela_cadastro(self):

        self.tela = TelaCadastro()
        self.tela.show()

        self.close()

    def verificar_login(self):

        usuario_digitado = self.txt_usuario.text().strip()
        senha_digitada = self.txt_senha.text()

        self.lbl_mensagem.clear()

        # Verifica campos vazios
        if not usuario_digitado or not senha_digitada:

            self.lbl_mensagem.setText(
                "Informe o usuário e a senha."
            )

            self.lbl_mensagem.setStyleSheet(
                "color: red;"
            )

            return

        conexao = None
        cursor = None

        try:

            # Conecta ao banco
            conexao = conectar()

            cursor = conexao.cursor()

            # Procura o usuário
            sql = """
                SELECT
                    id_usuarios,
                    nome,
                    login,
                    senha
                FROM usuarios
                WHERE login = %s
                LIMIT 1
            """

            cursor.execute(
                sql,
                (usuario_digitado,)
            )

            usuario = cursor.fetchone()

            # Usuário não encontrado
            if usuario is None:

                self.mostrar_login_invalido()

                return

            # Dados do usuário
            id_usuario = usuario[0]
            nome = usuario[1]
            login = usuario[2]
            senha_banco = usuario[3]

            # Converte o hash para bytes
            if isinstance(senha_banco, str):

                senha_hash = senha_banco.encode(
                    "utf-8"
                )

            else:

                senha_hash = bytes(
                    senha_banco
                )

            # Verifica a senha
            senha_correta = bcrypt.checkpw(
                senha_digitada.encode("utf-8"),
                senha_hash
            )

            if not senha_correta:

                self.mostrar_login_invalido()

                return

        except (ValueError, TypeError) as erro:

            print(
                "Erro ao verificar senha:",
                repr(erro)
            )

            self.lbl_mensagem.setText(
                "Erro ao verificar a senha."
            )

            self.lbl_mensagem.setStyleSheet(
                "color: orange;"
            )

            return

        except Exception as erro:

            print(
                "Erro no banco:",
                repr(erro)
            )

            self.lbl_mensagem.setText(
                "Erro ao acessar o banco."
            )

            self.lbl_mensagem.setStyleSheet(
                "color: orange;"
            )

            return

        finally:

            if cursor is not None:

                try:
                    cursor.close()
                except Exception:
                    pass

            if conexao is not None:

                try:
                    conexao.close()
                except Exception:
                    pass

        # Se chegou aqui, usuário e senha estão corretos
        self.abrir_dashboard(
            id_usuario,
            nome,
            login
        )

    def abrir_dashboard(
        self,
        id_usuario,
        nome,
        login
    ):

        print("------------------------------")
        print("LOGIN REALIZADO COM SUCESSO")
        print("ID:", id_usuario)
        print("Nome:", nome)
        print("Login:", login)
        print("------------------------------")

        try:

            self.tela = TelaDashboard()

            self.tela.show()

            self.close()

        except Exception as erro:

            print("------------------------------")
            print("ERRO AO ABRIR DASHBOARD")
            print(repr(erro))
            print("------------------------------")

            self.lbl_mensagem.setText(
                "Login correto. Erro ao abrir Dashboard."
            )

            self.lbl_mensagem.setStyleSheet(
                "color: orange;"
            )

    def mostrar_login_invalido(self):

        self.lbl_mensagem.setText(
            "Usuário ou senha incorretos."
        )

        self.lbl_mensagem.setStyleSheet(
            "color: red;"
        )


if __name__ == "__main__":

    app = QtWidgets.QApplication(
        sys.argv
    )

    janela = TelaLogin()

    janela.show()

    sys.exit(
        app.exec()
    )