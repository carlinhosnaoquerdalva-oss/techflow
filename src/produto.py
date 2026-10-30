from decimal import Decimal, InvalidOperation

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QAbstractItemView

from utils.cnn import conectar


class GerenciadorProdutos:
    def __init__(self, tela):
        self.tela = tela
        self.id_produto_selecionado = None

        # Modelo usado pelo QTableView de produtos.
        self.modelo = QStandardItemModel()
        self.modelo.setHorizontalHeaderLabels(
            [
                "Código",
                "Nome",
                "Descrição",
                "Categoria",
                "Preço",
                "Estoque",
            ]
        )
        self.tela.tableView_produtos.setModel(self.modelo)

        self.tela.tableView_produtos.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tela.tableView_produtos.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tela.tableView_produtos.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        # Liga os componentes da página de produtos aos métodos do CRUD.
        self.tela.btn_salvar_2.clicked.connect(self.salvar_produto)
        self.tela.btn_limpar_2.clicked.connect(self.limpar_campos)
        self.tela.btn_excluir_2.clicked.connect(self.excluir_produto)
        self.tela.tableView_produtos.doubleClicked.connect(
            self.carregar_campos_ao_duplo_clique
        )

        self.carregar_dados_na_tabela()

    def carregar_dados_na_tabela(self):
        """Consulta os produtos no MySQL e atualiza a tabela da interface."""
        self.modelo.removeRows(0, self.modelo.rowCount())
        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT
                    id_produtos,
                    nome,
                    descricao,
                    categoria,
                    preco,
                    estoque
                FROM produtos
                ORDER BY id_produtos
                """
            )

            for produto in cursor.fetchall():
                preco = produto[4]
                preco_formatado = (
                    f"{Decimal(str(preco)):.2f}" if preco is not None else "0.00"
                )
                linha = [
                    QStandardItem(str(produto[0] or "")),
                    QStandardItem(str(produto[1] or "")),
                    QStandardItem(str(produto[2] or "")),
                    QStandardItem(str(produto[3] or "")),
                    QStandardItem(preco_formatado),
                    QStandardItem(str(produto[5] if produto[5] is not None else 0)),
                ]
                self.modelo.appendRow(linha)

            self.tela.tableView_produtos.resizeColumnsToContents()
            self.tela.tableView_produtos.horizontalHeader().setStretchLastSection(True)

        except Exception as erro:
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Erro ao carregar produtos do banco:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def salvar_produto(self):
        """Insere um produto novo ou atualiza o produto carregado."""
        codigo_texto = (
            str(self.id_produto_selecionado)
            if self.id_produto_selecionado is not None
            else ""
        )
        nome = self.tela.edit_nome_produtos.text().strip()
        descricao = self.tela.edit_descricao_produtos.text().strip()
        categoria = self.tela.combo_categoria_produtos.currentText().strip()
        preco_texto = self.tela.edit_preco_produtos.text().strip().replace(",", ".")
        estoque_texto = self.tela.edit_estoque_produtos.text().strip()

        if not nome:
            QMessageBox.warning(self.tela, "Aviso", "Preencha o nome do produto.")
            self.tela.edit_nome_produtos.setFocus()
            return
        if not descricao:
            QMessageBox.warning(self.tela, "Aviso", "Preencha a descrição do produto.")
            self.tela.edit_descricao_produtos.setFocus()
            return
        if not categoria:
            QMessageBox.warning(self.tela, "Aviso", "Selecione a categoria do produto.")
            self.tela.combo_categoria.setFocus()
            return

        try:
            preco = Decimal(preco_texto)
            if preco < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Informe um preço válido e não negativo. Exemplo: 19,90.",
            )
            self.tela.edit_preco_produtos.setFocus()
            return

        try:
            estoque = int(estoque_texto)
            if estoque < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Informe o estoque como um número inteiro não negativo.",
            )
            self.tela.edit_estoque_produtos.setFocus()
            return

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            if codigo_texto:
                cursor.execute(
                    """
                    UPDATE produtos
                    SET nome = %s,
                        descricao = %s,
                        categoria = %s,
                        preco = %s,
                        estoque = %s
                    WHERE id_produtos = %s
                    """,
                    (
                        nome,
                        descricao,
                        categoria,
                        preco,
                        estoque,
                        int(codigo_texto),
                    ),
                )
                mensagem = (
                    "Produto atualizado com sucesso!"
                    if cursor.rowcount > 0
                    else "Nenhuma alteração foi realizada."
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO produtos
                        (nome, descricao, categoria, preco, estoque)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (nome, descricao, categoria, preco, estoque),
                )
                mensagem = "Produto cadastrado com sucesso!"

            conexao.commit()
            QMessageBox.information(self.tela, "Sucesso", mensagem)
            self.limpar_campos()
            self.carregar_dados_na_tabela()

        except ValueError:
            QMessageBox.warning(self.tela, "Aviso", "O código do produto é inválido.")
        except Exception as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Não foi possível salvar o produto:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_campos_ao_duplo_clique(self, index):
        """Copia para o formulário os dados da linha clicada."""
        linha = index.row()

        def texto(coluna):
            item = self.modelo.item(linha, coluna)
            return item.text() if item is not None else ""

        try:
            self.id_produto_selecionado = int(texto(0))
        except ValueError:
            self.id_produto_selecionado = None
            QMessageBox.warning(self.tela, "Aviso", "Código do produto inválido.")
            return
        self.tela.edit_nome_produtos.setText(texto(1))
        self.tela.edit_descricao_produtos.setText(texto(2))

        categoria = texto(3)
        indice_categoria = self.tela.combo_categoria.findText(categoria)
        if indice_categoria < 0 and categoria:
            self.tela.combo_categoria.addItem(categoria)
            indice_categoria = self.tela.combo_categoria.findText(categoria)
        if indice_categoria >= 0:
            self.tela.combo_categoria.setCurrentIndex(indice_categoria)

        self.tela.edit_preco_produtos.setText(texto(4).replace(".", ","))
        self.tela.edit_estoque_produtos.setText(texto(5))

    def excluir_produto(self):
        """Exclui o produto carregado ou a linha selecionada na tabela."""
        codigo_texto = (
            str(self.id_produto_selecionado)
            if self.id_produto_selecionado is not None
            else ""
        )

        if not codigo_texto:
            linhas = self.tela.tableView_produtos.selectionModel().selectedRows()
            if not linhas:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Selecione um produto na tabela.",
                )
                return

            item_id = self.modelo.item(linhas[0].row(), 0)
            if item_id is None:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Não foi possível identificar o produto.",
                )
                return
            codigo_texto = item_id.text()

        try:
            id_produto = int(codigo_texto)
        except ValueError:
            QMessageBox.warning(self.tela, "Aviso", "O código do produto é inválido.")
            return

        resposta = QMessageBox.question(
            self.tela,
            "Confirmar exclusão",
            f"Deseja realmente excluir o produto de código {id_produto}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                "DELETE FROM produtos WHERE id_produtos = %s",
                (id_produto,),
            )
            conexao.commit()

            if cursor.rowcount == 0:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Produto não encontrado no banco.",
                )
            else:
                QMessageBox.information(
                    self.tela,
                    "Sucesso",
                    "Produto excluído com sucesso!",
                )

            self.limpar_campos()
            self.carregar_dados_na_tabela()

        except Exception as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Não foi possível excluir o produto:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def limpar_campos(self):
        """Limpa o formulário e remove a seleção da tabela."""
        self.id_produto_selecionado = None
        self.tela.edit_nome_produtos.clear()
        self.tela.edit_descricao_produtos.clear()
        self.tela.edit_preco_produtos_produtos.clear()
        self.tela.edit_estoque_produtos_produtos.clear()

        if self.tela.combo_categoria.count() > 0:
            self.tela.combo_categoria.setCurrentIndex(0)

        self.tela.tableView_produtos.clearSelection()
        self.tela.edit_nome_produtos.setFocus()
