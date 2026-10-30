from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QAbstractItemView

from utils.cnn import conectar


class GerenciadorClientes:
    def __init__(self, tela):
        self.tela = tela

        # Modelo da tabela
        self.modelo = QStandardItemModel()
        self.modelo.setHorizontalHeaderLabels(
            [
                "CÃ³digo",
                "Nome",
                "CPF",
                "Telefone",
                "Email",
                "Cidade"
            ]
        )

        self.tela.tableView.setModel(self.modelo)

        # ConfiguraÃ§Ã£o da seleÃ§Ã£o da tabela
        self.tela.tableView.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.tela.tableView.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Conecta os botÃµes
        self.tela.btn_salvar.clicked.connect(
            self.salvar_cliente
        )

        self.tela.btn_limpar.clicked.connect(
            self.limpar_campos
        )

        self.tela.btn_excluir.clicked.connect(
            self.excluir_cliente
        )

        # Duplo clique na tabela
        self.tela.tableView.doubleClicked.connect(
            self.carregar_campos_ao_duplo_clique
        )

        # Carrega os clientes ao abrir a tela
        self.carregar_dados_na_tabela()

    def carregar_dados_na_tabela(self):
        """Carrega os clientes diretamente do banco MySQL remoto."""

        self.modelo.removeRows(
            0,
            self.modelo.rowCount()
        )

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            sql = """
                SELECT
                    id_clientes,
                    nome,
                    cpf,
                    telefone,
                    email,
                    cidade
                FROM clientes
                ORDER BY id_clientes
            """

            cursor.execute(sql)
            clientes = cursor.fetchall()

            for cliente in clientes:
                linha = [
                    QStandardItem(str(cliente[0] or "")),
                    QStandardItem(str(cliente[1] or "")),
                    QStandardItem(str(cliente[2] or "")),
                    QStandardItem(str(cliente[3] or "")),
                    QStandardItem(str(cliente[4] or "")),
                    QStandardItem(str(cliente[5] or ""))
                ]

                self.modelo.appendRow(linha)

            self.tela.tableView.resizeColumnsToContents()

        except Exception as erro:
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Erro ao carregar clientes do banco:\n{erro}"
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexao is not None:
                conexao.close()

    def salvar_cliente(self):
        """Cadastra um cliente novo ou atualiza um existente."""

        codigo_texto = (
            self.tela.edit_codigo.text().strip()
        )

        nome = self.tela.edit_nome.text().strip()
        cpf = self.tela.edit_cpf.text().strip()
        telefone = self.tela.edit_telefone.text().strip()
        email = self.tela.edit_email.text().strip()
        cidade = self.tela.edit_cidade.text().strip()

        if not nome:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o nome do cliente."
            )
            return

        if not cpf:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o CPF do cliente."
            )
            return

        if not telefone:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o telefone do cliente."
            )
            return

        if not email:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o email do cliente."
            )
            return

        if not cidade:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha a cidade do cliente."
            )
            return

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            if codigo_texto:
                # Atualiza um cliente existente
                sql = """
                    UPDATE clientes
                    SET
                        nome = %s,
                        cpf = %s,
                        telefone = %s,
                        email = %s,
                        cidade = %s
                    WHERE id_clientes = %s
                """

                cursor.execute(
                    sql,
                    (
                        nome,
                        cpf,
                        telefone,
                        email,
                        cidade,
                        int(codigo_texto)
                    )
                )

                if cursor.rowcount == 0:
                    mensagem = (
                        "Nenhuma alteraÃ§Ã£o foi realizada."
                    )
                else:
                    mensagem = (
                        "Cliente atualizado com sucesso!"
                    )

            else:
                # Cadastra um cliente novo
                sql = """
                    INSERT INTO clientes
                    (
                        nome,
                        cpf,
                        telefone,
                        email,
                        cidade
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """

                cursor.execute(
                    sql,
                    (
                        nome,
                        cpf,
                        telefone,
                        email,
                        cidade
                    )
                )

                mensagem = (
                    "Cliente cadastrado com sucesso!"
                )

            conexao.commit()

            QMessageBox.information(
                self.tela,
                "Sucesso",
                mensagem
            )

            self.limpar_campos()
            self.carregar_dados_na_tabela()

        except Exception as erro:
            if conexao is not None:
                conexao.rollback()

            QMessageBox.critical(
                self.tela,
                "Erro",
                f"NÃ£o foi possÃ­vel salvar o cliente:\n{erro}"
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexao is not None:
                conexao.close()

    def carregar_campos_ao_duplo_clique(self, index):
        """Carrega os dados da linha nos campos da tela."""

        linha = index.row()

        item_id = self.modelo.item(linha, 0)
        item_nome = self.modelo.item(linha, 1)
        item_cpf = self.modelo.item(linha, 2)
        item_telefone = self.modelo.item(linha, 3)
        item_email = self.modelo.item(linha, 4)
        item_cidade = self.modelo.item(linha, 5)

        self.tela.edit_codigo.setText(
            item_id.text() if item_id else ""
        )

        self.tela.edit_nome.setText(
            item_nome.text() if item_nome else ""
        )

        self.tela.edit_cpf.setText(
            item_cpf.text() if item_cpf else ""
        )

        self.tela.edit_telefone.setText(
            item_telefone.text() if item_telefone else ""
        )

        self.tela.edit_email.setText(
            item_email.text() if item_email else ""
        )

        self.tela.edit_cidade.setText(
            item_cidade.text() if item_cidade else ""
        )

    def excluir_cliente(self):
        """Exclui o cliente do banco MySQL remoto."""

        codigo_texto = (
            self.tela.edit_codigo.text().strip()
        )

        if not codigo_texto:
            linhas_selecionadas = (
                self.tela.tableView
                .selectionModel()
                .selectedRows()
            )

            if not linhas_selecionadas:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Selecione um cliente na tabela."
                )
                return

            linha = linhas_selecionadas[0].row()
            item_id = self.modelo.item(linha, 0)

            if item_id is None:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "NÃ£o foi possÃ­vel identificar o cliente."
                )
                return

            codigo_texto = item_id.text()

        try:
            id_cliente = int(codigo_texto)

        except ValueError:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "O cÃ³digo do cliente Ã© invÃ¡lido."
            )
            return

        resposta = QMessageBox.question(
            self.tela,
            "Confirmar exclusÃ£o",
            (
                "Deseja realmente excluir o cliente "
                f"de cÃ³digo {id_cliente}?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            sql = """
                DELETE FROM clientes
                WHERE id_clientes = %s
            """

            cursor.execute(
                sql,
                (id_cliente,)
            )

            conexao.commit()

            if cursor.rowcount == 0:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Cliente nÃ£o encontrado no banco."
                )

            else:
                QMessageBox.information(
                    self.tela,
                    "Sucesso",
                    "Cliente excluÃ­do com sucesso!"
                )

            self.limpar_campos()
            self.carregar_dados_na_tabela()

        except Exception as erro:
            if conexao is not None:
                conexao.rollback()

            QMessageBox.critical(
                self.tela,
                "Erro",
                f"NÃ£o foi possÃ­vel excluir o cliente:\n{erro}"
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexao is not None:
                conexao.close()

    def limpar_campos(self):
        """Limpa os campos da tela."""

        self.tela.edit_codigo.clear()
        self.tela.edit_nome.clear()
        self.tela.edit_cpf.clear()
        self.tela.edit_telefone.clear()
        self.tela.edit_email.clear()
        self.tela.edit_cidade.clear()

        self.tela.tableView.clearSelection()