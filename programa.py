import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QMessageBox, QProgressBar, QFrame,
    QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

class Combatiente:
    def __init__(self, nombre, fuerza, destreza, salud):
        self.nombre = nombre
        self.fuerza = fuerza
        self.destreza = destreza
        self.salud = salud
        self.max_salud = salud

    def recibir_daño(self, daño):
        self.salud = max(0, int(self.salud - daño))
        return self.salud

    def esta_vivo(self):
        return self.salud > 0

    def __repr__(self):
        return f"{self.nombre} (HP:{self.salud}/{self.max_salud} ATK:{self.fuerza} DEX:{self.destreza})"

CONFIG = {
    "HEAL_PERCENT": 0.25,
    "POINTS_PER_WIN": 3,
    "PLAYER_CRIT_CHANCE": 0.12,
    "ENEMY_CRIT_CHANCE": 0.08,
    "ENEMY_TURN_DELAY_MS": 700,
}

ENEMY_TEMPLATES = [
    Combatiente("Ars", 19, 15, 30),
    Combatiente("Becker", 22, 10, 40),
    Combatiente("Crixus", 25, 12, 50),
    Combatiente("Darius", 30, 8, 60),
    Combatiente("The Creator...", 100, 100, 100),
]

def calcular_prob_esquivar(dex_objetivo, dex_ataque):
    if dex_objetivo <= 0:
        return 0.05
    chance = dex_objetivo / (dex_objetivo + dex_ataque * 1.5)
    return max(0.05, min(0.6, chance))

class GameWindow(QMainWindow):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.player_name = player.nombre
        self.initial_player_stats = (player.fuerza, player.destreza, player.max_salud)
        
        self.enemy_templates = ENEMY_TEMPLATES
        self.guerreros = [Combatiente(e.nombre, e.fuerza, e.destreza, e.salud) for e in self.enemy_templates]
        
        self.idx_enemigo_actual = 0
        self.victorias = 0
        self.stat_points = 0
        self.en_combate = False
        self.enemy = None

        self.init_ui()
        self.aplicar_estilos()
        self.update_ui()

    def init_ui(self):
        self.setWindowTitle("Combate de Guerreros — Arena")
        self.resize(820, 600)
        self.setWindowIcon(QIcon("logo.png"))

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        title = QLabel("Arena de Combate")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        root_layout.addWidget(title)

        paneles_layout = QHBoxLayout()
        root_layout.addLayout(paneles_layout)

        self.frm_player = self._crear_panel_combatiente("Jugador")
        self.lbl_player_name, self.pbar_player, self.lbl_player_stats = self.frm_player.findChildren(QLabel)[0], self.frm_player.findChild(QProgressBar), self.frm_player.findChildren(QLabel)[1]
        paneles_layout.addWidget(self.frm_player)

        self.frm_enemy = self._crear_panel_combatiente("Enemigo")
        self.lbl_enemy_name, self.pbar_enemy, self.lbl_enemy_stats = self.frm_enemy.findChildren(QLabel)[0], self.frm_enemy.findChild(QProgressBar), self.frm_enemy.findChildren(QLabel)[1]
        paneles_layout.addWidget(self.frm_enemy)

        btns_layout = QHBoxLayout()
        root_layout.addLayout(btns_layout)

        self.btn_stats = QPushButton("Ver Mis Estadísticas")
        self.btn_stats.clicked.connect(self.show_stats)
        btns_layout.addWidget(self.btn_stats)

        self.btn_upgrade = QPushButton("Mejorar (0 Ptos)")
        self.btn_upgrade.clicked.connect(self.open_upgrade_menu)
        btns_layout.addWidget(self.btn_upgrade)
        
        self.btn_start = QPushButton("Iniciar Combate")
        self.btn_start.clicked.connect(self.start_combat)
        btns_layout.addWidget(self.btn_start)

        self.btn_attack = QPushButton("Atacar")
        self.btn_attack.clicked.connect(self.player_attack)
        btns_layout.addWidget(self.btn_attack)

        self.btn_run = QPushButton("Huir")
        self.btn_run.clicked.connect(self.run_from_enemy)
        btns_layout.addWidget(self.btn_run)

        self.btn_skip = QPushButton("Saltar Enemigo")
        self.btn_skip.clicked.connect(self.skip_enemy)
        btns_layout.addWidget(self.btn_skip)

        self.btn_play_again = QPushButton("Volver a Jugar")
        self.btn_play_again.clicked.connect(self.reset_game)
        self.btn_play_again.hide()
        root_layout.addWidget(self.btn_play_again)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        root_layout.addWidget(self.log, 1)

        footer = QLabel("Consejo: ¡Usa tus puntos de mejora sabiamente!")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(footer)

    def _crear_panel_combatiente(self, titulo_defecto):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        lbl_name = QLabel(titulo_defecto)
        lbl_name.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(lbl_name)

        pbar = QProgressBar()
        pbar.setFormat("HP: %v / %m")
        pbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(pbar)

        lbl_stats = QLabel("Stats")
        lbl_stats.setFont(QFont("Arial", 10))
        layout.addWidget(lbl_stats)

        return frame

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QLabel {
                color: #ECEFF4;
            }
            QPushButton {
                background-color: #4C566A;
                color: #ECEFF4;
                border: 1px solid #5E81AC;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5E81AC;
            }
            QPushButton:disabled {
                background-color: #3B4252;
                color: #4C566A;
                border-color: #434C5E;
            }
            #BtnUpgrade {
                background-color: #A3BE8C;
                color: #2E3440;
                border-color: #8FBCBB;
                font-weight: bold;
            }
            #BtnUpgrade:hover {
                background-color: #B48EAD;
            }
            #BtnUpgrade:disabled {
                background-color: #3B4252;
                color: #4C566A;
                border-color: #434C5E;
            }
            #BtnPlayAgain {
                background-color: #BF616A;
                color: #ECEFF4;
                font-weight: bold;
                padding: 12px;
            }
            #BtnPlayAgain:hover {
                background-color: #D08770;
            }
            QTextEdit {
                background-color: #3B4252;
                color: #A3BE8C;
                font-family: Consolas, monaco, monospace;
                font-size: 14px;
                border: 1px solid #434C5E;
                border-radius: 5px;
            }
            QProgressBar {
                border: 1px solid #4C566A;
                border-radius: 5px;
                text-align: center;
                color: #2E3440;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 4px;
            }
            QFrame {
                border: 1px solid #434C5E;
                border-radius: 5px;
            }
        """)
        self.btn_upgrade.setObjectName("BtnUpgrade")
        self.btn_play_again.setObjectName("BtnPlayAgain")

    def update_ui(self):
        self.lbl_player_name.setText(f"{self.player.nombre}")
        self.pbar_player.setMaximum(self.player.max_salud)
        self.pbar_player.setValue(self.player.salud)
        self.lbl_player_stats.setText(f"ATK: {self.player.fuerza} | DEX: {self.player.destreza} | Victorias: {self.victorias} | Ptos: {self.stat_points}")
        self.btn_upgrade.setText(f"Mejorar ({self.stat_points} Ptos)")

        if self.idx_enemigo_actual < len(self.guerreros):
            en = self.guerreros[self.idx_enemigo_actual]
            self.lbl_enemy_name.setText(f"Enemigo {self.idx_enemigo_actual + 1}: {en.nombre}")
            self.pbar_enemy.setMaximum(en.max_salud)
            self.pbar_enemy.setValue(en.salud)
            self.lbl_enemy_stats.setText(f"ATK: {en.fuerza} | DEX: {en.destreza}")
        else:
            self.lbl_enemy_name.setText("¡Arena completada!")
            self.pbar_enemy.setValue(0)
            self.lbl_enemy_stats.setText("")

        fuera_de_combate = not self.en_combate and self.player.esta_vivo()
        hay_enemigos = self.idx_enemigo_actual < len(self.guerreros)

        self.btn_start.setEnabled(fuera_de_combate and hay_enemigos)
        self.btn_attack.setEnabled(self.en_combate)
        self.btn_run.setEnabled(self.en_combate)
        self.btn_skip.setEnabled(fuera_de_combate and hay_enemigos)
        self.btn_stats.setEnabled(self.player.esta_vivo())
        self.btn_upgrade.setEnabled(fuera_de_combate and self.stat_points > 0)

    def append_log(self, text):
        self.log.append(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def show_stats(self):
        stats_texto = (
            f"Salud:   {self.player.salud}/{self.player.max_salud}\n"
            f"Fuerza:   {self.player.fuerza}\n"
            f"Destreza: {self.player.destreza}\n"
            f"Puntos:   {self.stat_points}"
        )
        QMessageBox.information(self, "Tus Estadísticas", f"<pre>{stats_texto}</pre>")

    def open_upgrade_menu(self):
        if self.stat_points <= 0:
            QMessageBox.information(self, "Mejoras", "No tienes puntos de mejora.")
            return

        opciones = [
            f"Fuerza (+1) - Coste: 1 pto",
            f"Destreza (+1) - Coste: 1 pto",
            f"Salud Máxima (+5) - Coste: 1 pto"
        ]
        
        coste = 1

        opcion, ok = QInputDialog.getItem(self, "Menú de Mejoras",
                                          f"Tienes {self.stat_points} puntos.\n¿Qué quieres mejorar?",
                                          opciones, 0, False)

        if ok and opcion:
            if self.stat_points < coste:
                QMessageBox.warning(self, "Error", "No tienes suficientes puntos.")
                return

            self.stat_points -= coste

            if "Fuerza" in opcion:
                self.player.fuerza += 1
                self.append_log(f"💪 Has mejorado tu Fuerza a {self.player.fuerza}.")
            elif "Destreza" in opcion:
                self.player.destreza += 1
                self.append_log(f"💨 Has mejorado tu Destreza a {self.player.destreza}.")
            elif "Salud Máxima" in opcion:
                self.player.max_salud += 5
                self.player.salud += 5
                self.append_log(f"❤️ Has mejorado tu Salud Máxima a {self.player.max_salud}.")

            self.update_ui()

            if self.stat_points > 0:
                reply = QMessageBox.question(self, "Seguir mejorando",
                                             f"Te quedan {self.stat_points} puntos.\n¿Quieres mejorar algo más?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    QTimer.singleShot(100, self.open_upgrade_menu)

    def skip_enemy(self):
        if self.en_combate: return
        self.append_log(f"🚶 Has decidido no enfrentarte a {self.guerreros[self.idx_enemigo_actual].nombre}.")
        self.idx_enemigo_actual += 1
        self.update_ui()

    def start_combat(self):
        if self.idx_enemigo_actual >= len(self.guerreros) or self.en_combate:
            return

        self.enemy = self.guerreros[self.idx_enemigo_actual]
        self.en_combate = True
        self.append_log(f"⚔️ ¡Comienza el combate contra {self.enemy.nombre}! ⚔️")
        self.update_ui()

    def player_attack(self):
        if not self.en_combate: return

        self.btn_attack.setEnabled(False)

        prob_enemy_esq = calcular_prob_esquivar(self.enemy.destreza, self.player.destreza)
        if random.random() < prob_enemy_esq:
            self.append_log(f"💨 Tu ataque falló. {self.enemy.nombre} lo esquivó (prob: {prob_enemy_esq:.0%}).")
        else:
            crit = random.random() < CONFIG["PLAYER_CRIT_CHANCE"]
            daño = int(self.player.fuerza * (2 if crit else 1))
            self.enemy.recibir_daño(daño)
            crit_msg = " ¡GOLPE CRÍTICO! " if crit else ""
            self.append_log(f"💥 Atacas a {self.enemy.nombre}.{crit_msg}Le infliges {daño} de daño.")

        self.update_ui()

        if not self.enemy.esta_vivo():
            self.handle_victory()
        else:
            QTimer.singleShot(CONFIG["ENEMY_TURN_DELAY_MS"], self.enemy_turn)

    def enemy_turn(self):
        if not self.en_combate: return

        prob_player_esq = calcular_prob_esquivar(self.player.destreza, self.enemy.destreza)
        if random.random() < prob_player_esq:
            self.append_log(f"🛡️ ¡Esquivaste el ataque de {self.enemy.nombre}! (prob: {prob_player_esq:.0%}).")
        else:
            crit = random.random() < CONFIG["ENEMY_CRIT_CHANCE"]
            daño = int(self.enemy.fuerza * (2 if crit else 1))
            self.player.recibir_daño(daño)
            crit_msg = " ¡CRÍTICO! " if crit else " "
            self.append_log(f"🩸 {self.enemy.nombre} te ataca.{crit_msg}Recibes {daño} de daño.")
        
        self.update_ui()

        if not self.player.esta_vivo():
            self.handle_defeat()
        else:
            self.btn_attack.setEnabled(True)

    def run_from_enemy(self):
        if not self.en_combate: return
        
        chance = calcular_prob_esquivar(self.player.destreza + 5, self.enemy.destreza)
        if random.random() < chance:
            self.append_log("🏃‍♂️ Has huido con éxito del combate.")
            self.end_combat(huida=True)
        else:
            self.append_log("🚫 Intentaste huir, pero fallaste. El enemigo aprovecha para atacar.")
            self.btn_attack.setEnabled(False)
            self.btn_run.setEnabled(False)
            QTimer.singleShot(CONFIG["ENEMY_TURN_DELAY_MS"], self.enemy_turn)

    def handle_victory(self):
        self.victorias += 1
        curacion = int(self.player.max_salud * CONFIG["HEAL_PERCENT"])
        puntos_ganados = CONFIG["POINTS_PER_WIN"]
        self.stat_points += puntos_ganados

        self.player.salud = min(self.player.max_salud, self.player.salud + curacion)
        
        self.append_log(f"🏆 ¡Has derrotado a {self.enemy.nombre}!")
        self.append_log(f"Recompensa: +{curacion} HP, ¡+{puntos_ganados} Puntos de Mejora!")

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("¡Victoria!")
        msg_box.setText(f"¡Has derrotado a {self.enemy.nombre}!")
        msg_box.exec()

        self.end_combat()

    def handle_defeat(self):
        self.append_log("💀 Has sido derrotado. La arena te reclama. 💀")
        self.en_combate = False

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Derrota")
        msg_box.setText("Has perdido en combate. Fin de la partida.")
        msg_box.exec()
        
        self.update_ui()
        self.show_end_game_buttons()

    def end_combat(self, huida=False):
        self.en_combate = False
        self.idx_enemigo_actual += 1
        
        if self.idx_enemigo_actual >= len(self.guerreros):
            self.append_log("🎉 ¡Felicidades! ¡Has derrotado a todos los guerreros de la arena! 🎉")
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("¡Has ganado!")
            msg_box.setText("¡Felicidades! ¡Has derrotado a todos los guerreros de la arena!")
            msg_box.exec()
            self.show_end_game_buttons()
            
        elif not huida:
             self.append_log("Preparas tu siguiente combate...")
        
        self.update_ui()

    def show_end_game_buttons(self):
        self.btn_attack.setEnabled(False)
        self.btn_run.setEnabled(False)
        self.btn_skip.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_stats.setEnabled(False)
        self.btn_upgrade.setEnabled(False)
        self.btn_play_again.show()

    def reset_game(self):
        self.player.nombre = self.player_name
        self.player.fuerza, self.player.destreza, self.player.max_salud = self.initial_player_stats
        self.player.salud = self.player.max_salud
        
        self.guerreros = [Combatiente(e.nombre, e.fuerza, e.destreza, e.salud) for e in self.enemy_templates]
        self.idx_enemigo_actual = 0
        self.victorias = 0
        self.stat_points = 0
        self.en_combate = False
        self.enemy = None
        
        self.log.clear()
        self.append_log(f"¡Un nuevo desafío comienza para {self.player.nombre}!")
        
        self.btn_play_again.hide()
        
        self.update_ui()

def main():
    app = QApplication(sys.argv)
    
    nombre, ok = QInputDialog.getText(None, "Nombre del jugador", "Introduce tu nombre:", text="Héroe")
    if not (ok and nombre.strip()):
        nombre = "Héroe Anónimo"

    jugador = Combatiente(
        nombre=nombre.strip(),
        fuerza=20,
        destreza=15,
        salud=50
    )

    ventana = GameWindow(player=jugador)
    ventana.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()