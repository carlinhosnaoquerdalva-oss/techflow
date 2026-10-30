from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox
import bcrypt

from utils.cnn import conectar


class TelaCadastro(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        uic.loadUi("views/cadastro.ui", self)

        # Oculta os caracteres digitados nos campos de senha
        self.entry_senha.setEchoMode(
            QtWidgets.QLineEdit.EchoMode.Password
        )

        self.entry_conf_senha.setEchoMode(
            QtWidgets.QLineEdit.EchoMode.Password
        )

        # Evento do botão cadastrar
        self.btn_cadastrar.clicked.connect(
            self.cadastrar_usuario
        )

    def cadastrar_usuario(self):

        # Obtém os valores dos campos da interface
        nome = self.entry_nome.text().strip()
        login = self.entry_login.text().strip()
        senha = self.entry_senha.text()
        confirmar = self.entry_conf_senha.text()

        # Verifica se todos os campos foram preenchidos
        if not nome or not login or not senha or not confirmar:
            QMessageBox.warning(
                self,
                "Aviso",
                "Preencha todos os campos."
            )
            return

        # Verifica se as duas senhas são iguais
        if senha != confirmar:
            QMessageBox.warning(
                self,
                "Aviso",
                "As senhas não coincidem."
            )
            return

        try:

            # Conecta ao banco de dados
            conexao = conectar()
            cursor = conexao.cursor()

            # Verifica se o login já existe
            sql = """
                SELECT id_usuarios
                FROM usuarios
                WHERE login = %s
            """

            cursor.execute(sql, (login,))

            if cursor.fetchone():

                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Login já cadastrado."
                )

                cursor.close()
                conexao.close()

                return

            # Gera o hash da senha usando bcrypt
            senha_hash = bcrypt.hashpw(
                senha.encode("utf-8"),
                bcrypt.gensalt()
            )

            # Cadastra o novo usuário
            sql = """
                INSERT INTO usuarios
                (
                    nome,
                    login,
                    senha
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
            """

            cursor.execute(
                sql,
                (
                    nome,
                    login,
                    senha_hash.decode("utf-8")
                )
            )

            conexao.commit()

            cursor.close()
            conexao.close()

            QMessageBox.information(
                self,
                "Sucesso",
                "Usuário cadastrado com sucesso!"
            )

            # Abre a tela de login
            self.login = QtWidgets.QWidget()
            uic.loadUi("views/login.ui", self.login)

            self.login.show()
            self.close()

        except Exception as erro:

            QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )