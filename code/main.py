import gi
import sqlite3 as sql
import datetime

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk


class Utils:
    """
    Classe de suporte para a classe principal Handler
    """

    @staticmethod
    def css(css_path, window):
        """
        Função para aplicar css de um arquivo para uma janela específica
        Todos os elementos que serão modificados precisam ter os seus IDs referenciados no arquivo css
        Depois passar a janela na qual esses elementos estão inseridos
        """
        css_provider = gtk.CssProvider()
        css_provider.load_from_path(css_path)
        style_context = gtk.StyleContext()
        style_context.add_provider_for_screen(window.get_default(), css_provider,
                                              gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    @staticmethod
    def dialog_box(window, primary_label, secondary_label, titulo: str, mensagem: str):
        """
        Função para criar caixa de diálogo que será usada para mensagens de erro e outras
        """
        primary_label.set_text(titulo)
        secondary_label.set_text(mensagem)
        window.show_all()
        window.run()
        window.hide()

    @staticmethod
    def yes_no(bt_yes, bt_no):
        if bt_yes.get_active():
            return 1
        elif bt_no.get_active():
            return 0

    @staticmethod
    def sim_nao(state):
        if state == 1:
            return "Sim"
        else:
            return "Não"

    @staticmethod
    def true_false(state):
        if state == "Sim":
            return 1
        elif state == "sim":
            return 1
        elif state == "Não":
            return 0
        elif state == "não":
            return 0
        elif state == "nao":
            return 0
        elif state == "não":
            return 0


ui_path = "programa.glade"
builder = gtk.Builder.new_from_file(ui_path)


# Carreguei um objeto Builder a partir do arquivo XML gerado pelo Glade
# Com isso todos os objetos que eu defini no Glade também foram carregados


class Handler(Utils):
    def __init__(self):
        super().__init__()

        # --> Conexão ao banco de dados sql
        self.dados = sql.connect("data.sqlite")
        self.cursor = self.dados.cursor()

        # --> Janela principal
        self.window_main = builder.get_object("window_main")
        self.toolbar_main_window = builder.get_object("toolbar_main_window")
        self.searchbar = builder.get_object("searchbar")
        self.entry_searchbar = builder.get_object("entry_searchbar")
        self.bt_restore = builder.get_object("bt_restore")
        self.bt_add = builder.get_object("bt_add")
        self.bt_remove = builder.get_object("bt_remove")
        self.grade = builder.get_object("grade")
        self.lst_grade = builder.get_object("lst_grade_main_window")
        self.window_main.show_all()
        self.restore()

        # --> Grade
        self.grade = builder.get_object("grade")
        self.lst_grade = builder.get_object("lst_grade_main_window")
        self.render_word = builder.get_object("render_word")
        self.palavra = builder.get_object("palavra")
        self.frase = builder.get_object("frase")
        self.significado = builder.get_object("significado")
        self.order_controller = 0

        # --> Variáveis globais para uso em múltiplas funções
        self.cod_selecteds = []

        # --> Janela de diálogos popup
        self.window_dialog = builder.get_object("msg_dialog")
        self.label_dialog_primary = builder.get_object("dialog_primary_label")
        self.label_dialog_secondary = builder.get_object("dialog_secondary_label")

        # --> Janela Adicionar palavras
        self.window_addwords = builder.get_object("window_addwords")
        self.entry_add_word = builder.get_object("entry_word")
        self.entry_add_phrase = builder.get_object("entry_phrase")
        self.entry_add_meaning = builder.get_object("entry_meaning")
        self.bt_gravar = builder.get_object("bt_gravar")
        self.bt_yes = builder.get_object("bt_yes")
        self.bt_no = builder.get_object("bt_no")
        self.state_yes_no = 1

    #######################################################################
    # --> Botões da janela principal
    def search(self, *args):
        """
        Função que pesquisa o que tem escrito na SearchEntry em tempo real
        Sinais conectados:
        entry_searchbar: activate
        entry_searchbar: search-changed
        """
        try:
            self.lst_grade.clear()
            pesquisa = str(self.entry_searchbar.get_text().upper())
            self.cursor.execute(f"SELECT word, phrase, meaning, data, cod, in_anki "
                                f"FROM vocabulary WHERE word LIKE '%{pesquisa}%'")
            results = self.cursor.fetchall()
            for result in results:
                selecao = False
                word = result[0]
                phrase = result[1]
                meaning = result[2]
                date = result[3]
                cod = str(result[4])
                in_anki = self.sim_nao(result[5])
                pesquisa = [selecao, word, phrase, meaning, date, cod, in_anki]
                self.lst_grade.append(pesquisa)
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro", f"Erro ao pesquisar:\n{ex}")

    def restore(self, *args):
        """
        Função que é executada ao clicar o o botão restaurar
        Sinais conectados:
        bt_restore: clicked
        """
        try:
            self.lst_grade.clear()
            self.cursor.execute("SELECT word, phrase, meaning, data, cod, in_anki FROM vocabulary")
            results = self.cursor.fetchall()
            for item in results:
                selecao = False
                word = item[0]
                phrase = item[1]
                meaning = item[2]
                date = item[3]
                cod = str(item[4])
                in_anki = self.sim_nao(item[5])
                pesquisa = [selecao, word, phrase, meaning, date, cod, in_anki]
                self.lst_grade.append(pesquisa)
            self.entry_searchbar.set_text("")
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro", f"Erro ao restaurar tabela:\n{ex}")

    ########################################################################
    # --> Função de selecionar itens na grade

    def select(self, *args):
        """
        Função que serve para selecionar itens na grade
        Quando é cliclado no botão CellRendererToggle o sinal faz trocar o valor de False para True
        Também é enviado o Cod (ID), automaticamente gerado,
        que é referenciado como Primary Key no banco de dados,
        para a variável global self.cod_selecteds.
        Essa variável global conterá a Primary Key de todos os elementos selecionados da lista
        Ela será usada em outras funções por exemplo para remover esse elementos ou alterá-los.
        Sinais conectados:
        render_select: toggled
        """
        try:
            linha = args[1]
            valor_default = False
            valor_novo = True
            valor_atual = self.grade.get_model()[linha][0]
            if valor_atual == valor_default:
                self.grade.get_model()[linha][0] = valor_novo
                self.cod_selecteds.append(self.grade.get_model()[linha][5])
            else:
                self.grade.get_model()[linha][0] = valor_default
                self.cod_selecteds.remove(self.grade.get_model()[linha][5])

        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro!", f"Ocorreu um erro: {ex}")

    def clicar_bt_add(self, *args):
        """
        Função que vai abrir a janela Adicionar palavras
        É aberta com o botão: bt_add
        Sinais conectados:
        bt_add: clicked
        """
        self.window_addwords.set_transient_for(self.window_main)
        self.window_addwords.show_all()

    def clicar_bt_export(self, *args):
        """
        Função que vai abrir a janela para criar um arquivo e salvar as
        frases em txt para o anki
        """
        try:
            dialog = gtk.FileChooserDialog(title="Salvar como", parent=self.window_main,
                                           action=gtk.FileChooserAction.SAVE)
            dialog.add_button("Salvar", gtk.ResponseType.OK)
            dialog.add_button("Cancelar", gtk.ResponseType.CANCEL)
            response = dialog.run()
            if response == gtk.ResponseType.OK:
                with open(dialog.get_filename(), "w") as arq:
                    try:
                        for c in self.cod_selecteds:
                            query = f"SELECT phrase, meaning FROM vocabulary WHERE cod IS {c}"
                            self.cursor.execute(query)
                            result = self.cursor.fetchall()
                            arq.write(str(result[0][0]) + "\t" + str(result[0][1]) + "\n")
                    except Exception as ex:
                        self.dialog_box(self.window_dialog, self.label_dialog_primary,
                                        self.label_dialog_secondary,
                                        "Erro!", f"Ocorreu um erro: {ex}")
                dialog.hide()
            elif response == gtk.ResponseType.CANCEL:
                dialog.hide()
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary,
                            self.label_dialog_secondary,
                            "Erro!", f"Ocorreu um erro: {ex}")
    def clicar_bt_remove(self, *args):
        """
        Função que remove todos os itens selecionados na grade ao clicar o botão Remover
        Utiliza da variávei global self.cod_selecteds
        Sinais conectados:
        bt_remove: clicked
        """
        try:
            for key in self.cod_selecteds:
                query = f"DELETE FROM vocabulary WHERE cod = {key}"
                self.cursor.execute(query)
                self.dados.commit()
                self.restore()
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary,
                            self.label_dialog_secondary, "Erro!", f"Ocorreu um erro: {ex}")

    def edit_word(self, *args):
        """
        Função que permite a edição na coluna Palavra na tabela
        Sinais conectados:
        render_word = edited
        """
        try:
            linha = args[1]
            edicao = str(args[2])
            key = int(self.grade.get_model()[linha][5])
            query = f"UPDATE vocabulary SET word = '{edicao}' WHERE cod = {key}"
            self.cursor.execute(query)
            self.dados.commit()
            self.grade.get_model()[linha][1] = edicao
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary,
                            self.label_dialog_secondary, "Erro!", f"Ocorreu um erro: {ex}")

    def edit_phrase(self, *args):
        """
        Função que permite a edição na coluna Frase na tabela
        Sinais conectados:
        render_phrase = edited
        """
        try:
            linha = args[1]
            edicao = str(args[2])
            key = int(self.grade.get_model()[linha][5])
            query = f"UPDATE vocabulary SET phrase = '{edicao}' WHERE cod = {key}"
            self.cursor.execute(query)
            self.dados.commit()
            self.grade.get_model()[linha][2] = edicao
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary,
                            self.label_dialog_secondary, "Erro!", f"Ocorreu um erro: {ex}")

    def edit_meanings(self, *args):
        """
        Função que permite a edição na coluna Significados na tabela
        Sinais conectados:
        render_meanings = edited
        """
        try:
            linha = args[1]
            edicao = str(args[2])
            key = int(self.grade.get_model()[linha][5])
            query = f"UPDATE vocabulary SET meaning = '{edicao}' WHERE cod = {key}"
            self.cursor.execute(query)
            self.dados.commit()
            self.grade.get_model()[linha][3] = edicao
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary,
                            self.label_dialog_secondary, "Erro!", f"Ocorreu um erro: {ex}")

    def edit_in_anki(self, *args):
        """
        Edita a coluna No anki na grade da Janela Principal
        """
        try:
            linha = args[1]
            value = self.true_false(args[2])
            key = int(self.grade.get_model()[linha][5])
            query = f"UPDATE vocabulary SET in_anki = {value} WHERE cod = {key}"
            self.cursor.execute(query)
            self.dados.commit()
            self.grade.get_model()[linha][6] = args[2]
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary,
                            self.label_dialog_secondary, "Erro!", f"Ocorreu um erro: {ex}")

    def order(self, *args):
        try:
            if self.order_controller == 0:
                self.order_controller = 1
                self.restore()
                word_line = []
                for a in self.lst_grade:
                    linha = a.path.get_indices()[0]
                    word_line.append([a[1], linha])
                word_line.sort()
                new = []
                for n in word_line:
                    new.append(n[1])
                self.lst_grade.reorder(new)
            elif self.order_controller == 1:
                self.order_controller = 2
                self.restore()
                word_line = []
                for a in self.lst_grade:
                    linha = a.path.get_indices()[0]
                    word_line.append([a[1], linha])
                word_line.sort(reverse=True)
                new = []
                for n in word_line:
                    new.append(n[1])
                self.lst_grade.reorder(new)
            elif self.order_controller == 2:
                self.order_controller = 0
                self.restore()
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro", f"Erro ao restaurar tabela:\n{ex}")

    ###############################################################
    # --> Botões da janela Exportar

    def clicar_bt_salvar(self, *args):
        pass

    def clicar_bt_cancelar(self, *args):
        pass

    ###############################################################
    # --> Botões da janela Adicionar palavras

    def commit(self, *args):
        """
        Função acionada ao apertar o botão Gravar na janela Adicionar palavras
        Pega tudo o que está escrito nas entries dessa janela e envia para o banco de dados sqlite
        Sinais conectados:
        bt_gravar: clicked
        """
        try:
            palavra = self.entry_add_word.get_text()
            frase = self.entry_add_phrase.get_text()
            meaning = self.entry_add_meaning.get_text()
            data_hoje = datetime.date.today()
            in_anki = self.state_yes_no
            valores = [palavra, frase, meaning, data_hoje, in_anki]
            self.cursor.execute("INSERT INTO vocabulary(word, phrase, meaning, data, in_anki) "
                                "values(?, ?, ?, ?, ?)", valores)
            self.dados.commit()
            self.entry_add_word.set_text("")
            self.entry_add_meaning.set_text("")
            self.entry_add_phrase.set_text("")
            data_hoje = None
            self.restore()
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Sucesso!", "Os dados gravados com sucesso.")

        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro!", f"Ocorreu um erro ao gravar os dados: {ex}")

    def tg_bt_yes(self, *args):
        """
        Função que é disparada ao selecionar a opção Sim na janela Adicionar palavras
        Ela muda a variável global state_yes_no para 1 (True)
        Sinais conectados:
        bt_yes: toggled
        """
        try:
            self.state_yes_no = self.yes_no(self.bt_yes, self.bt_no)
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro!", f"Ocorreu um erro: {ex}")

    def tg_bt_no(self, *args):
        """
        Função que é disparada ao selecionar a opção Não na janela Adicionar palavras
        Ela muda a variável global state_yes_no para 0 (False)
        Sinais conectados:
        bt_no: toggled
        """
        try:
            self.state_yes_no = self.yes_no(self.bt_yes, self.bt_no)
        except Exception as ex:
            self.dialog_box(self.window_dialog, self.label_dialog_primary, self.label_dialog_secondary,
                            "Erro!", f"Ocorreu um erro: {ex}")

    #############################################################
    # --> Funções para fechar janelas

    @staticmethod
    def destroy_window_main(*args):
        gtk.main_quit()

    def close_window_addwords(self, *args):
        self.window_addwords.hide()
        self.window_main.set_transient_for(self.window_addwords)
        return True

    def close_popup(self, *args):
        self.window_dialog.hide()
        return True


if __name__ == "__main__":
    builder.connect_signals(Handler())
    gtk.main()
