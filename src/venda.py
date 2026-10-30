from decimal import Decimal

from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QAbstractItemView, QMessageBox

from utils.cnn import conectar


class GerenciadorVendas:
    """Controla o CRUD de vendas da pagina de vendas do dashboard."""

    def __init__(self, tela):
        self.tela = tela
        self.id_venda_selecionada = None
        self.coluna_produto_vendas = self._detectar_coluna_produto_vendas()

        self.modelo = QStandardItemModel()
        self.modelo.setHorizontalHeaderLabels(
            [
                "Codigo",
                "Cliente",
                "Produto",
                "Quantidade",
                "Valor total",
                "Data da venda",
            ]
        )

        self.tela.tableView_vendas_4.setModel(self.modelo)
        self.tela.tableView_vendas_4.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tela.tableView_vendas_4.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tela.tableView_vendas_4.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.tela.btn_salvar_7.clicked.connect(self.salvar_venda)
        self.tela.btn_limpar_7.clicked.connect(self.limpar_campos)
        self.tela.btn_excluir_9.clicked.connect(self.excluir_venda)
        self.tela.tableView_vendas_4.doubleClicked.connect(
            self.carregar_campos_ao_duplo_clique
        )

        self.carregar_clientes()
        self.carregar_produtos()
        self.carregar_dados_na_tabela()

    def _detectar_coluna_produto_vendas(self):
        """Confere a estrutura da tabela vendas na mesma conexao usada pelo programa."""
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("SELECT DATABASE()")
            banco = cursor.fetchone()[0]
            cursor.execute("SHOW COLUMNS FROM vendas")
            colunas = {linha[0] for linha in cursor.fetchall()}

            if "id_produtos" in colunas:
                return "id_produtos"
            if "id_produto" in colunas:
                return "id_produto"

            raise RuntimeError(
                "A tabela vendas do banco "
                f"'{banco}' nao possui a coluna id_produtos. "
                f"Colunas encontradas: {', '.join(sorted(colunas))}"
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_clientes(self):
        """Carrega clientes no combo, guardando o ID em userData."""
        self.tela.combo_clientes_vendas.clear()
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT id_clientes, nome FROM clientes ORDER BY nome"
            )
            for id_cliente, nome in cursor.fetchall():
                self.tela.combo_clientes_vendas.addItem(
                    str(nome), int(id_cliente)
                )
        except Exception as erro:
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Erro ao carregar clientes:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_produtos(self):
        """Carrega produtos no combo, guardando ID, preco e estoque."""
        self.tela.combo_produto_vendas.clear()
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT id_produtos, nome, preco, estoque
                FROM produtos
                ORDER BY nome
                """
            )
            for id_produto, nome, preco, estoque in cursor.fetchall():
                dados = {
                    "id": int(id_produto),
                    "preco": Decimal(str(preco or 0)),
                    "estoque": int(estoque or 0),
                }
                texto = f"{nome} - R$ {dados['preco']:.2f}"
                self.tela.combo_produto_vendas.addItem(texto, dados)
        except Exception as erro:
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Erro ao carregar produtos:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_dados_na_tabela(self):
        """Lista vendas e mostra os nomes do cliente e do produto."""
        self.modelo.removeRows(0, self.modelo.rowCount())
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                f"""
                SELECT
                    v.id_vendas,
                    c.nome,
                    p.nome,
                    v.quantidade,
                    v.valor_total,
                    v.data_venda,
                    v.id_clientes,
                    v.{self.coluna_produto_vendas}
                FROM vendas AS v
                INNER JOIN clientes AS c
                    ON c.id_clientes = v.id_clientes
                INNER JOIN produtos AS p
                    ON p.id_produtos = v.{self.coluna_produto_vendas}
                ORDER BY v.id_vendas DESC
                """
            )

            for venda in cursor.fetchall():
                data_texto = (
                    venda[5].strftime("%d/%m/%Y %H:%M:%S")
                    if hasattr(venda[5], "strftime")
                    else str(venda[5] or "")
                )
                itens = [
                    QStandardItem(str(venda[0])),
                    QStandardItem(str(venda[1])),
                    QStandardItem(str(venda[2])),
                    QStandardItem(str(venda[3])),
                    QStandardItem(f"R$ {Decimal(str(venda[4] or 0)):.2f}"),
                    QStandardItem(data_texto),
                ]
                # IDs usados ao carregar a venda para edicao.
                itens[0].setData(int(venda[6]) if venda[6] is not None else None, 256)
                itens[0].setData(int(venda[7]) if venda[7] is not None else None, 257)
                self.modelo.appendRow(itens)

            self.tela.tableView_vendas_4.resizeColumnsToContents()
            self.tela.tableView_vendas_4.horizontalHeader().setStretchLastSection(True)
            self.atualizar_total_geral()
        except Exception as erro:
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Erro ao carregar vendas:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def atualizar_total_geral(self):
        """Mostra a soma de valor_total de todas as vendas."""
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("SELECT COALESCE(SUM(valor_total), 0) FROM vendas")
            total = Decimal(str(cursor.fetchone()[0] or 0))
            self.tela.edit_total_vendas_.setText(f"R$ {total:.2f}")
            self.tela.edit_total_vendas_.setReadOnly(True)
        except Exception:
            self.tela.edit_total_vendas_.setText("R$ 0,00")
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def salvar_venda(self):
        """Insere uma venda ou atualiza a venda selecionada."""
        id_cliente = self.tela.combo_clientes_vendas.currentData()
        dados_produto = self.tela.combo_produto_vendas.currentData()
        quantidade_texto = self.tela.edit_quantidade_vendas.text().strip()

        if id_cliente is None:
            QMessageBox.warning(self.tela, "Aviso", "Selecione um cliente.")
            return
        if not dados_produto:
            QMessageBox.warning(self.tela, "Aviso", "Selecione um produto.")
            return

        try:
            quantidade = int(quantidade_texto)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Informe uma quantidade inteira maior que zero.",
            )
            self.tela.edit_quantidade_vendas.setFocus()
            return

        id_produto = int(dados_produto["id"])
        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            # Bloqueia o produto durante a conferencia e alteracao do estoque.
            cursor.execute(
                "SELECT preco, estoque FROM produtos WHERE id_produtos = %s FOR UPDATE",
                (id_produto,),
            )
            produto = cursor.fetchone()
            if produto is None:
                raise ValueError("Produto nao encontrado no banco.")

            preco = Decimal(str(produto[0] or 0))
            estoque_atual = int(produto[1] or 0)

            if self.id_venda_selecionada is None:
                if quantidade > estoque_atual:
                    raise ValueError(
                        f"Estoque insuficiente. Disponivel: {estoque_atual}."
                    )

                valor_total = preco * quantidade
                cursor.execute(
                    f"""
                    INSERT INTO vendas
                        (id_clientes, {self.coluna_produto_vendas}, quantidade, valor_total, data_venda)
                    VALUES (%s, %s, %s, %s, NOW())
                    """,
                    (id_cliente, id_produto, quantidade, valor_total),
                )
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - %s WHERE id_produtos = %s",
                    (quantidade, id_produto),
                )
                mensagem = "Venda registrada com sucesso!"
            else:
                cursor.execute(
                    f"""
                    SELECT {self.coluna_produto_vendas}, quantidade
                    FROM vendas
                    WHERE id_vendas = %s
                    FOR UPDATE
                    """,
                    (self.id_venda_selecionada,),
                )
                venda_antiga = cursor.fetchone()
                if venda_antiga is None:
                    raise ValueError("Venda nao encontrada no banco.")

                produto_antigo = int(venda_antiga[0])
                quantidade_antiga = int(venda_antiga[1])

                # Devolve ao estoque a quantidade da venda anterior.
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque + %s WHERE id_produtos = %s",
                    (quantidade_antiga, produto_antigo),
                )

                # Reconsulta e bloqueia o estoque do novo produto apos a devolucao.
                cursor.execute(
                    "SELECT preco, estoque FROM produtos WHERE id_produtos = %s FOR UPDATE",
                    (id_produto,),
                )
                novo_produto = cursor.fetchone()
                preco = Decimal(str(novo_produto[0] or 0))
                estoque_disponivel = int(novo_produto[1] or 0)
                if quantidade > estoque_disponivel:
                    raise ValueError(
                        f"Estoque insuficiente. Disponivel: {estoque_disponivel}."
                    )

                valor_total = preco * quantidade
                cursor.execute(
                    f"""
                    UPDATE vendas
                    SET id_clientes = %s,
                        {self.coluna_produto_vendas} = %s,
                        quantidade = %s,
                        valor_total = %s
                    WHERE id_vendas = %s
                    """,
                    (
                        id_cliente,
                        id_produto,
                        quantidade,
                        valor_total,
                        self.id_venda_selecionada,
                    ),
                )
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - %s WHERE id_produtos = %s",
                    (quantidade, id_produto),
                )
                mensagem = "Venda atualizada com sucesso!"

            conexao.commit()
            QMessageBox.information(self.tela, "Sucesso", mensagem)
            self.limpar_campos()
            self.carregar_produtos()
            self.carregar_dados_na_tabela()
        except Exception as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Nao foi possivel salvar a venda:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_campos_ao_duplo_clique(self, index):
        """Carrega uma venda para edicao ao dar duplo clique na tabela."""
        linha = index.row()
        item_id = self.modelo.item(linha, 0)
        item_quantidade = self.modelo.item(linha, 3)
        if item_id is None:
            return

        self.id_venda_selecionada = int(item_id.text())
        id_cliente = item_id.data(256)
        id_produto = item_id.data(257)

        indice_cliente = self.tela.combo_clientes_vendas.findData(id_cliente)
        if indice_cliente >= 0:
            self.tela.combo_clientes_vendas.setCurrentIndex(indice_cliente)

        for indice in range(self.tela.combo_produto_vendas.count()):
            dados = self.tela.combo_produto_vendas.itemData(indice)
            if dados and dados.get("id") == id_produto:
                self.tela.combo_produto_vendas.setCurrentIndex(indice)
                break

        self.tela.edit_quantidade_vendas.setText(
            item_quantidade.text() if item_quantidade is not None else ""
        )
        self.tela.btn_salvar_7.setText("Atualizar Venda")

    def excluir_venda(self):
        """Exclui a venda selecionada e devolve sua quantidade ao estoque."""
        linhas = self.tela.tableView_vendas_4.selectionModel().selectedRows()
        if self.id_venda_selecionada is None and not linhas:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Selecione uma venda na tabela.",
            )
            return

        if self.id_venda_selecionada is not None:
            id_venda = self.id_venda_selecionada
        else:
            item_id = self.modelo.item(linhas[0].row(), 0)
            if item_id is None:
                return
            id_venda = int(item_id.text())

        resposta = QMessageBox.question(
            self.tela,
            "Confirmar exclusao",
            f"Deseja realmente excluir a venda de codigo {id_venda}?",
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
                f"""
                SELECT {self.coluna_produto_vendas}, quantidade
                FROM vendas
                WHERE id_vendas = %s
                FOR UPDATE
                """,
                (id_venda,),
            )
            venda = cursor.fetchone()
            if venda is None:
                raise ValueError("Venda nao encontrada no banco.")

            cursor.execute(
                "UPDATE produtos SET estoque = estoque + %s WHERE id_produtos = %s",
                (int(venda[1]), int(venda[0])),
            )
            cursor.execute(
                "DELETE FROM vendas WHERE id_vendas = %s",
                (id_venda,),
            )
            conexao.commit()

            QMessageBox.information(
                self.tela,
                "Sucesso",
                "Venda excluida com sucesso!",
            )
            self.limpar_campos()
            self.carregar_produtos()
            self.carregar_dados_na_tabela()
        except Exception as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Nao foi possivel excluir a venda:\n{erro}",
            )
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def limpar_campos(self):
        self.id_venda_selecionada = None
        self.tela.edit_quantidade_vendas.clear()
        if self.tela.combo_clientes_vendas.count() > 0:
            self.tela.combo_clientes_vendas.setCurrentIndex(0)
        if self.tela.combo_produto_vendas.count() > 0:
            self.tela.combo_produto_vendas.setCurrentIndex(0)
        self.tela.tableView_vendas_4.clearSelection()
        self.tela.btn_salvar_7.setText("Registrar Venda")
        self.tela.edit_quantidade_vendas.setFocus()
