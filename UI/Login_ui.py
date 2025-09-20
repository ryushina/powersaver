# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Login.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QStatusBar, QWidget)

class Ui_Login(object):
    def setupUi(self, Login):
        if not Login.objectName():
            Login.setObjectName(u"Login")
        Login.resize(378, 200)
        Login.setMinimumSize(QSize(378, 200))
        Login.setMaximumSize(QSize(389, 200))
        self.centralwidget = QWidget(Login)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setMinimumSize(QSize(389, 179))
        self.centralwidget.setMaximumSize(QSize(389, 179))
        self.gridLayoutWidget = QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(20, 30, 351, 71))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.le_Password = QLineEdit(self.gridLayoutWidget)
        self.le_Password.setObjectName(u"le_Password")
        self.le_Password.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout.addWidget(self.le_Password, 2, 1, 1, 1)

        self.label_2 = QLabel(self.gridLayoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.label = QLabel(self.gridLayoutWidget)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 1, 1, 1, 1)

        self.le_Username = QLineEdit(self.gridLayoutWidget)
        self.le_Username.setObjectName(u"le_Username")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.le_Username.sizePolicy().hasHeightForWidth())
        self.le_Username.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.le_Username, 0, 1, 1, 1)

        self.btn_Login = QPushButton(self.centralwidget)
        self.btn_Login.setObjectName(u"btn_Login")
        self.btn_Login.setGeometry(QRect(10, 130, 171, 31))
        self.btn_Cancel = QPushButton(self.centralwidget)
        self.btn_Cancel.setObjectName(u"btn_Cancel")
        self.btn_Cancel.setGeometry(QRect(190, 130, 171, 31))
        Login.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(Login)
        self.statusbar.setObjectName(u"statusbar")
        Login.setStatusBar(self.statusbar)

        self.retranslateUi(Login)

        QMetaObject.connectSlotsByName(Login)
    # setupUi

    def retranslateUi(self, Login):
        Login.setWindowTitle(QCoreApplication.translate("Login", u"Login Form", None))
        self.label_2.setText(QCoreApplication.translate("Login", u"Password", None))
        self.label.setText(QCoreApplication.translate("Login", u"Username", None))
        self.btn_Login.setText(QCoreApplication.translate("Login", u"Login", None))
        self.btn_Cancel.setText(QCoreApplication.translate("Login", u"Cancel", None))
    # retranslateUi

