import sys

from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
)

from src.cliente import GerenciadorClientes
from src.produto import GerenciadorProdutos
from src.venda import GerenciadorVendas


class TelaDashboard(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        # Carrega a interface
        uic.loadUi("views/dashboard.ui", self)

        # ----------------------------------------
        # Menu lateral
        # ----------------------------------------

        self.largura_menu_aberto = 211
        self.largura_menu_fechado = 0
        self.menu_aberto = True

        self.menu_lateral.setMinimumWidth(
            self.largura_menu_aberto
        )

        self.menu_lateral.setMaximumWidth(
            self.largura_menu_aberto
        )

        # ----------------------------------------
        # Botão para abrir/fechar menu
        # ----------------------------------------

        self.drop_button.clicked.connect(
            self.alternar_menu
        )

        # ----------------------------------------
        # QStackedWidget
        #
        # Nome definido no dashboard.ui:
        # conteudo_principal
        # ----------------------------------------

        self.conteudo_principal.setCurrentIndex(0)

        # Dashboard
        self.button_home.clicked.connect(
            lambda:
            self.conteudo_principal.setCurrentIndex(0)
        )

        # Cadastro de clientes
        self.cadastro_cliente.clicked.connect(
            lambda:
            self.conteudo_principal.setCurrentIndex(1)
        )

        # Cadastro de produtos
        self.cadastro_produto.clicked.connect(
            lambda:
            self.conteudo_principal.setCurrentIndex(2)
        )

        # Cadastro de vendas
        self.cadastro_vendas.clicked.connect(
            lambda:
            self.conteudo_principal.setCurrentIndex(3)
        )

        # ----------------------------------------
        # Gerenciador de clientes
        # ----------------------------------------

        self.gerenciador_clientes = (
            GerenciadorClientes(self)
        )
        self.gerenciador_produtos = (
            GerenciadorProdutos(self)
        )
        self.gerenciador_vendas = GerenciadorVendas(self)
    def alternar_menu(self):

        # Animação da largura mínima
        anim_min = QPropertyAnimation(
            self.menu_lateral,
            b"minimumWidth"
        )

        # Animação da largura máxima
        anim_max = QPropertyAnimation(
            self.menu_lateral,
            b"maximumWidth"
        )

        for animacao in (anim_min, anim_max):

            animacao.setDuration(300)

            animacao.setEasingCurve(
                QEasingCurve.Type.InOutCubic
            )

        # ----------------------------------------
        # Se estiver aberto, fecha
        # ----------------------------------------

        if self.menu_aberto:

            inicio = self.largura_menu_aberto
            fim = self.largura_menu_fechado

        # ----------------------------------------
        # Se estiver fechado, abre
        # ----------------------------------------

        else:

            inicio = self.largura_menu_fechado
            fim = self.largura_menu_aberto

        anim_min.setStartValue(inicio)
        anim_min.setEndValue(fim)

        anim_max.setStartValue(inicio)
        anim_max.setEndValue(fim)

        self.menu_aberto = not self.menu_aberto

        # Mantém referência da animação
        self.animacao = QParallelAnimationGroup(
            self
        )

        self.animacao.addAnimation(
            anim_min
        )

        self.animacao.addAnimation(
            anim_max
        )

        self.animacao.start()


# ==================================================
# Permite testar o dashboard diretamente
# ==================================================

if __name__ == "__main__":

    app = QtWidgets.QApplication(
        sys.argv
    )

    janela = TelaDashboard()

    janela.show()

    sys.exit(
        app.exec()
    )