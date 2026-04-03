# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDoubleSpinBox,
    QGridLayout, QGroupBox, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMenuBar, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QStatusBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1360, 860)
        self.actionSaveDatabase = QAction(MainWindow)
        self.actionSaveDatabase.setObjectName(u"actionSaveDatabase")
        self.actionSaveDatabaseAs = QAction(MainWindow)
        self.actionSaveDatabaseAs.setObjectName(u"actionSaveDatabaseAs")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(self.centralwidget)
        self.headerLabel.setObjectName(u"headerLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.headerLabel.sizePolicy().hasHeightForWidth())
        self.headerLabel.setSizePolicy(sizePolicy)
        self.headerLabel.setMaximumSize(QSize(16777215, 36))
        self.headerLabel.setStyleSheet(u"font-size: 20px; font-weight: 600; padding: 4px 0;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.subHeaderLabel = QLabel(self.centralwidget)
        self.subHeaderLabel.setObjectName(u"subHeaderLabel")
        sizePolicy.setHeightForWidth(self.subHeaderLabel.sizePolicy().hasHeightForWidth())
        self.subHeaderLabel.setSizePolicy(sizePolicy)
        self.subHeaderLabel.setMaximumSize(QSize(16777215, 44))
        self.subHeaderLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.subHeaderLabel)

        self.mainSplitter = QSplitter(self.centralwidget)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Horizontal)
        self.leftPanel = QWidget(self.mainSplitter)
        self.leftPanel.setObjectName(u"leftPanel")
        self.leftPanelLayout = QVBoxLayout(self.leftPanel)
        self.leftPanelLayout.setObjectName(u"leftPanelLayout")
        self.leftPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.workbenchTabWidget = QTabWidget(self.leftPanel)
        self.workbenchTabWidget.setObjectName(u"workbenchTabWidget")
        self.setupTab = QWidget()
        self.setupTab.setObjectName(u"setupTab")
        self.setupTabLayout = QVBoxLayout(self.setupTab)
        self.setupTabLayout.setObjectName(u"setupTabLayout")
        self.pathsGroupBox = QGroupBox(self.setupTab)
        self.pathsGroupBox.setObjectName(u"pathsGroupBox")
        self.gridLayoutPaths = QGridLayout(self.pathsGroupBox)
        self.gridLayoutPaths.setObjectName(u"gridLayoutPaths")
        self.storageLabel = QLabel(self.pathsGroupBox)
        self.storageLabel.setObjectName(u"storageLabel")

        self.gridLayoutPaths.addWidget(self.storageLabel, 0, 0, 1, 1)

        self.storagePathEdit = QLineEdit(self.pathsGroupBox)
        self.storagePathEdit.setObjectName(u"storagePathEdit")

        self.gridLayoutPaths.addWidget(self.storagePathEdit, 0, 1, 1, 1)

        self.browseStorageButton = QPushButton(self.pathsGroupBox)
        self.browseStorageButton.setObjectName(u"browseStorageButton")

        self.gridLayoutPaths.addWidget(self.browseStorageButton, 0, 2, 1, 1)

        self.templateLabel = QLabel(self.pathsGroupBox)
        self.templateLabel.setObjectName(u"templateLabel")

        self.gridLayoutPaths.addWidget(self.templateLabel, 1, 0, 1, 1)

        self.templatePathEdit = QLineEdit(self.pathsGroupBox)
        self.templatePathEdit.setObjectName(u"templatePathEdit")

        self.gridLayoutPaths.addWidget(self.templatePathEdit, 1, 1, 1, 1)

        self.browseTemplateButton = QPushButton(self.pathsGroupBox)
        self.browseTemplateButton.setObjectName(u"browseTemplateButton")

        self.gridLayoutPaths.addWidget(self.browseTemplateButton, 1, 2, 1, 1)

        self.inputLabel = QLabel(self.pathsGroupBox)
        self.inputLabel.setObjectName(u"inputLabel")

        self.gridLayoutPaths.addWidget(self.inputLabel, 2, 0, 1, 1)

        self.inputPathEdit = QLineEdit(self.pathsGroupBox)
        self.inputPathEdit.setObjectName(u"inputPathEdit")

        self.gridLayoutPaths.addWidget(self.inputPathEdit, 2, 1, 1, 1)

        self.browseInputButton = QPushButton(self.pathsGroupBox)
        self.browseInputButton.setObjectName(u"browseInputButton")

        self.gridLayoutPaths.addWidget(self.browseInputButton, 2, 2, 1, 1)


        self.setupTabLayout.addWidget(self.pathsGroupBox)

        self.templateToolsGroupBox = QGroupBox(self.setupTab)
        self.templateToolsGroupBox.setObjectName(u"templateToolsGroupBox")
        self.gridLayoutTemplateTools = QGridLayout(self.templateToolsGroupBox)
        self.gridLayoutTemplateTools.setObjectName(u"gridLayoutTemplateTools")
        self.validateTemplateButton = QPushButton(self.templateToolsGroupBox)
        self.validateTemplateButton.setObjectName(u"validateTemplateButton")

        self.gridLayoutTemplateTools.addWidget(self.validateTemplateButton, 0, 0, 1, 3)

        self.exportTemplateJsonButton = QPushButton(self.templateToolsGroupBox)
        self.exportTemplateJsonButton.setObjectName(u"exportTemplateJsonButton")

        self.gridLayoutTemplateTools.addWidget(self.exportTemplateJsonButton, 1, 0, 1, 3)

        self.exportTemplateExcelButton = QPushButton(self.templateToolsGroupBox)
        self.exportTemplateExcelButton.setObjectName(u"exportTemplateExcelButton")

        self.gridLayoutTemplateTools.addWidget(self.exportTemplateExcelButton, 2, 0, 1, 3)

        self.saveDebugBundleButton = QPushButton(self.templateToolsGroupBox)
        self.saveDebugBundleButton.setObjectName(u"saveDebugBundleButton")

        self.gridLayoutTemplateTools.addWidget(self.saveDebugBundleButton, 3, 0, 1, 3)


        self.setupTabLayout.addWidget(self.templateToolsGroupBox)

        self.setupSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.setupTabLayout.addItem(self.setupSpacer)

        self.workbenchTabWidget.addTab(self.setupTab, "")
        self.importTab = QWidget()
        self.importTab.setObjectName(u"importTab")
        self.importTabLayout = QVBoxLayout(self.importTab)
        self.importTabLayout.setObjectName(u"importTabLayout")
        self.importGroupBox = QGroupBox(self.importTab)
        self.importGroupBox.setObjectName(u"importGroupBox")
        self.verticalLayoutImport = QVBoxLayout(self.importGroupBox)
        self.verticalLayoutImport.setObjectName(u"verticalLayoutImport")
        self.importButton = QPushButton(self.importGroupBox)
        self.importButton.setObjectName(u"importButton")

        self.verticalLayoutImport.addWidget(self.importButton)

        self.importHintLabel = QLabel(self.importGroupBox)
        self.importHintLabel.setObjectName(u"importHintLabel")
        self.importHintLabel.setWordWrap(True)

        self.verticalLayoutImport.addWidget(self.importHintLabel)


        self.importTabLayout.addWidget(self.importGroupBox)

        self.storageOverviewGroupBox = QGroupBox(self.importTab)
        self.storageOverviewGroupBox.setObjectName(u"storageOverviewGroupBox")
        self.verticalLayoutStorageOverview = QVBoxLayout(self.storageOverviewGroupBox)
        self.verticalLayoutStorageOverview.setObjectName(u"verticalLayoutStorageOverview")
        self.refreshStorageViewButton = QPushButton(self.storageOverviewGroupBox)
        self.refreshStorageViewButton.setObjectName(u"refreshStorageViewButton")

        self.verticalLayoutStorageOverview.addWidget(self.refreshStorageViewButton)

        self.deleteSelectedRowsButton = QPushButton(self.storageOverviewGroupBox)
        self.deleteSelectedRowsButton.setObjectName(u"deleteSelectedRowsButton")

        self.verticalLayoutStorageOverview.addWidget(self.deleteSelectedRowsButton)

        self.storageSummaryLabel = QLabel(self.storageOverviewGroupBox)
        self.storageSummaryLabel.setObjectName(u"storageSummaryLabel")
        self.storageSummaryLabel.setWordWrap(True)

        self.verticalLayoutStorageOverview.addWidget(self.storageSummaryLabel)

        self.storageTableWidget = QTableWidget(self.storageOverviewGroupBox)
        if (self.storageTableWidget.columnCount() < 1):
            self.storageTableWidget.setColumnCount(1)
        __qtablewidgetitem = QTableWidgetItem()
        self.storageTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        self.storageTableWidget.setObjectName(u"storageTableWidget")
        self.storageTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.storageTableWidget.setAlternatingRowColors(True)
        self.storageTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.storageTableWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.storageTableWidget.setSortingEnabled(True)

        self.verticalLayoutStorageOverview.addWidget(self.storageTableWidget)


        self.importTabLayout.addWidget(self.storageOverviewGroupBox)

        self.importSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.importTabLayout.addItem(self.importSpacer)

        self.workbenchTabWidget.addTab(self.importTab, "")
        self.goldenTab = QWidget()
        self.goldenTab.setObjectName(u"goldenTab")
        self.goldenTabLayout = QVBoxLayout(self.goldenTab)
        self.goldenTabLayout.setObjectName(u"goldenTabLayout")
        self.goldenGroupBox = QGroupBox(self.goldenTab)
        self.goldenGroupBox.setObjectName(u"goldenGroupBox")
        self.gridLayoutGolden = QGridLayout(self.goldenGroupBox)
        self.gridLayoutGolden.setObjectName(u"gridLayoutGolden")
        self.goldenNameLabel = QLabel(self.goldenGroupBox)
        self.goldenNameLabel.setObjectName(u"goldenNameLabel")

        self.gridLayoutGolden.addWidget(self.goldenNameLabel, 0, 0, 1, 1)

        self.goldenNameEdit = QLineEdit(self.goldenGroupBox)
        self.goldenNameEdit.setObjectName(u"goldenNameEdit")

        self.gridLayoutGolden.addWidget(self.goldenNameEdit, 0, 1, 1, 2)

        self.referenceDimsLabel = QLabel(self.goldenGroupBox)
        self.referenceDimsLabel.setObjectName(u"referenceDimsLabel")

        self.gridLayoutGolden.addWidget(self.referenceDimsLabel, 1, 0, 1, 1)

        self.referenceDimsEdit = QLineEdit(self.goldenGroupBox)
        self.referenceDimsEdit.setObjectName(u"referenceDimsEdit")

        self.gridLayoutGolden.addWidget(self.referenceDimsEdit, 1, 1, 1, 2)

        self.filtersLabel = QLabel(self.goldenGroupBox)
        self.filtersLabel.setObjectName(u"filtersLabel")

        self.gridLayoutGolden.addWidget(self.filtersLabel, 2, 0, 1, 1)

        self.filtersEdit = QPlainTextEdit(self.goldenGroupBox)
        self.filtersEdit.setObjectName(u"filtersEdit")
        self.filtersEdit.setMaximumHeight(88)

        self.gridLayoutGolden.addWidget(self.filtersEdit, 2, 1, 1, 2)

        self.thresholdModeLabel = QLabel(self.goldenGroupBox)
        self.thresholdModeLabel.setObjectName(u"thresholdModeLabel")

        self.gridLayoutGolden.addWidget(self.thresholdModeLabel, 3, 0, 1, 1)

        self.thresholdModeComboBox = QComboBox(self.goldenGroupBox)
        self.thresholdModeComboBox.addItem("")
        self.thresholdModeComboBox.addItem("")
        self.thresholdModeComboBox.addItem("")
        self.thresholdModeComboBox.setObjectName(u"thresholdModeComboBox")

        self.gridLayoutGolden.addWidget(self.thresholdModeComboBox, 3, 1, 1, 1)

        self.centerMethodLabel = QLabel(self.goldenGroupBox)
        self.centerMethodLabel.setObjectName(u"centerMethodLabel")

        self.gridLayoutGolden.addWidget(self.centerMethodLabel, 4, 0, 1, 1)

        self.centerMethodComboBox = QComboBox(self.goldenGroupBox)
        self.centerMethodComboBox.addItem("")
        self.centerMethodComboBox.addItem("")
        self.centerMethodComboBox.setObjectName(u"centerMethodComboBox")

        self.gridLayoutGolden.addWidget(self.centerMethodComboBox, 4, 1, 1, 1)

        self.relativeLimitLabel = QLabel(self.goldenGroupBox)
        self.relativeLimitLabel.setObjectName(u"relativeLimitLabel")

        self.gridLayoutGolden.addWidget(self.relativeLimitLabel, 5, 0, 1, 1)

        self.relativeLimitSpinBox = QDoubleSpinBox(self.goldenGroupBox)
        self.relativeLimitSpinBox.setObjectName(u"relativeLimitSpinBox")
        self.relativeLimitSpinBox.setDecimals(4)
        self.relativeLimitSpinBox.setMaximum(999999999.000000000000000)
        self.relativeLimitSpinBox.setSingleStep(0.050000000000000)
        self.relativeLimitSpinBox.setValue(0.200000000000000)

        self.gridLayoutGolden.addWidget(self.relativeLimitSpinBox, 5, 1, 1, 1)

        self.sigmaMultiplierLabel = QLabel(self.goldenGroupBox)
        self.sigmaMultiplierLabel.setObjectName(u"sigmaMultiplierLabel")

        self.gridLayoutGolden.addWidget(self.sigmaMultiplierLabel, 6, 0, 1, 1)

        self.sigmaMultiplierSpinBox = QDoubleSpinBox(self.goldenGroupBox)
        self.sigmaMultiplierSpinBox.setObjectName(u"sigmaMultiplierSpinBox")
        self.sigmaMultiplierSpinBox.setDecimals(4)
        self.sigmaMultiplierSpinBox.setMaximum(999999999.000000000000000)
        self.sigmaMultiplierSpinBox.setSingleStep(0.500000000000000)
        self.sigmaMultiplierSpinBox.setValue(3.000000000000000)

        self.gridLayoutGolden.addWidget(self.sigmaMultiplierSpinBox, 6, 1, 1, 1)

        self.buildGoldenButton = QPushButton(self.goldenGroupBox)
        self.buildGoldenButton.setObjectName(u"buildGoldenButton")

        self.gridLayoutGolden.addWidget(self.buildGoldenButton, 7, 0, 1, 3)

        self.goldenPathLabel = QLabel(self.goldenGroupBox)
        self.goldenPathLabel.setObjectName(u"goldenPathLabel")

        self.gridLayoutGolden.addWidget(self.goldenPathLabel, 8, 0, 1, 1)

        self.goldenPathEdit = QLineEdit(self.goldenGroupBox)
        self.goldenPathEdit.setObjectName(u"goldenPathEdit")

        self.gridLayoutGolden.addWidget(self.goldenPathEdit, 8, 1, 1, 1)

        self.browseGoldenButton = QPushButton(self.goldenGroupBox)
        self.browseGoldenButton.setObjectName(u"browseGoldenButton")

        self.gridLayoutGolden.addWidget(self.browseGoldenButton, 8, 2, 1, 1)


        self.goldenTabLayout.addWidget(self.goldenGroupBox)

        self.goldenSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.goldenTabLayout.addItem(self.goldenSpacer)

        self.workbenchTabWidget.addTab(self.goldenTab, "")
        self.analysisTab = QWidget()
        self.analysisTab.setObjectName(u"analysisTab")
        self.analysisTabLayout = QVBoxLayout(self.analysisTab)
        self.analysisTabLayout.setObjectName(u"analysisTabLayout")
        self.analysisGroupBox = QGroupBox(self.analysisTab)
        self.analysisGroupBox.setObjectName(u"analysisGroupBox")
        self.gridLayoutAnalysis = QGridLayout(self.analysisGroupBox)
        self.gridLayoutAnalysis.setObjectName(u"gridLayoutAnalysis")
        self.goldenSourceLabel = QLabel(self.analysisGroupBox)
        self.goldenSourceLabel.setObjectName(u"goldenSourceLabel")

        self.gridLayoutAnalysis.addWidget(self.goldenSourceLabel, 0, 0, 1, 1)

        self.goldenSourceComboBox = QComboBox(self.analysisGroupBox)
        self.goldenSourceComboBox.addItem("")
        self.goldenSourceComboBox.addItem("")
        self.goldenSourceComboBox.setObjectName(u"goldenSourceComboBox")

        self.gridLayoutAnalysis.addWidget(self.goldenSourceComboBox, 0, 1, 1, 2)

        self.outlierFailModeLabel = QLabel(self.analysisGroupBox)
        self.outlierFailModeLabel.setObjectName(u"outlierFailModeLabel")

        self.gridLayoutAnalysis.addWidget(self.outlierFailModeLabel, 1, 0, 1, 1)

        self.outlierFailModeComboBox = QComboBox(self.analysisGroupBox)
        self.outlierFailModeComboBox.addItem("")
        self.outlierFailModeComboBox.addItem("")
        self.outlierFailModeComboBox.addItem("")
        self.outlierFailModeComboBox.addItem("")
        self.outlierFailModeComboBox.setObjectName(u"outlierFailModeComboBox")

        self.gridLayoutAnalysis.addWidget(self.outlierFailModeComboBox, 1, 1, 1, 2)

        self.zThresholdLabel = QLabel(self.analysisGroupBox)
        self.zThresholdLabel.setObjectName(u"zThresholdLabel")

        self.gridLayoutAnalysis.addWidget(self.zThresholdLabel, 2, 0, 1, 1)

        self.zThresholdSpinBox = QDoubleSpinBox(self.analysisGroupBox)
        self.zThresholdSpinBox.setObjectName(u"zThresholdSpinBox")
        self.zThresholdSpinBox.setDecimals(3)
        self.zThresholdSpinBox.setMinimum(0.001000000000000)
        self.zThresholdSpinBox.setMaximum(999.000000000000000)
        self.zThresholdSpinBox.setSingleStep(0.100000000000000)
        self.zThresholdSpinBox.setValue(3.500000000000000)

        self.gridLayoutAnalysis.addWidget(self.zThresholdSpinBox, 2, 1, 1, 2)

        self.analysisScopeLabel = QLabel(self.analysisGroupBox)
        self.analysisScopeLabel.setObjectName(u"analysisScopeLabel")

        self.gridLayoutAnalysis.addWidget(self.analysisScopeLabel, 3, 0, 1, 1)

        self.analysisScopeComboBox = QComboBox(self.analysisGroupBox)
        self.analysisScopeComboBox.addItem("")
        self.analysisScopeComboBox.addItem("")
        self.analysisScopeComboBox.addItem("")
        self.analysisScopeComboBox.addItem("")
        self.analysisScopeComboBox.setObjectName(u"analysisScopeComboBox")

        self.gridLayoutAnalysis.addWidget(self.analysisScopeComboBox, 3, 1, 1, 2)

        self.analysisSampleIdsLabel = QLabel(self.analysisGroupBox)
        self.analysisSampleIdsLabel.setObjectName(u"analysisSampleIdsLabel")

        self.gridLayoutAnalysis.addWidget(self.analysisSampleIdsLabel, 4, 0, 1, 1)

        self.analysisSampleIdsEdit = QLineEdit(self.analysisGroupBox)
        self.analysisSampleIdsEdit.setObjectName(u"analysisSampleIdsEdit")

        self.gridLayoutAnalysis.addWidget(self.analysisSampleIdsEdit, 4, 1, 1, 2)

        self.analysisExcludeSampleIdsLabel = QLabel(self.analysisGroupBox)
        self.analysisExcludeSampleIdsLabel.setObjectName(u"analysisExcludeSampleIdsLabel")

        self.gridLayoutAnalysis.addWidget(self.analysisExcludeSampleIdsLabel, 5, 0, 1, 1)

        self.analysisExcludeSampleIdsEdit = QLineEdit(self.analysisGroupBox)
        self.analysisExcludeSampleIdsEdit.setObjectName(u"analysisExcludeSampleIdsEdit")

        self.gridLayoutAnalysis.addWidget(self.analysisExcludeSampleIdsEdit, 5, 1, 1, 2)

        self.analysisNodesLabel = QLabel(self.analysisGroupBox)
        self.analysisNodesLabel.setObjectName(u"analysisNodesLabel")

        self.gridLayoutAnalysis.addWidget(self.analysisNodesLabel, 6, 0, 1, 1)

        self.analysisNodesEdit = QLineEdit(self.analysisGroupBox)
        self.analysisNodesEdit.setObjectName(u"analysisNodesEdit")

        self.gridLayoutAnalysis.addWidget(self.analysisNodesEdit, 6, 1, 1, 2)

        self.analysisExcludeNodesLabel = QLabel(self.analysisGroupBox)
        self.analysisExcludeNodesLabel.setObjectName(u"analysisExcludeNodesLabel")

        self.gridLayoutAnalysis.addWidget(self.analysisExcludeNodesLabel, 7, 0, 1, 1)

        self.analysisExcludeNodesEdit = QLineEdit(self.analysisGroupBox)
        self.analysisExcludeNodesEdit.setObjectName(u"analysisExcludeNodesEdit")

        self.gridLayoutAnalysis.addWidget(self.analysisExcludeNodesEdit, 7, 1, 1, 2)

        self.analysisImportsLabel = QLabel(self.analysisGroupBox)
        self.analysisImportsLabel.setObjectName(u"analysisImportsLabel")

        self.gridLayoutAnalysis.addWidget(self.analysisImportsLabel, 8, 0, 1, 1)

        self.refreshAnalysisImportsButton = QPushButton(self.analysisGroupBox)
        self.refreshAnalysisImportsButton.setObjectName(u"refreshAnalysisImportsButton")

        self.gridLayoutAnalysis.addWidget(self.refreshAnalysisImportsButton, 8, 1, 1, 2)

        self.analysisImportsListWidget = QListWidget(self.analysisGroupBox)
        self.analysisImportsListWidget.setObjectName(u"analysisImportsListWidget")
        self.analysisImportsListWidget.setMinimumHeight(110)
        self.analysisImportsListWidget.setMaximumHeight(160)

        self.gridLayoutAnalysis.addWidget(self.analysisImportsListWidget, 9, 0, 1, 3)

        self.outputLabel = QLabel(self.analysisGroupBox)
        self.outputLabel.setObjectName(u"outputLabel")

        self.gridLayoutAnalysis.addWidget(self.outputLabel, 10, 0, 1, 1)

        self.outputPathEdit = QLineEdit(self.analysisGroupBox)
        self.outputPathEdit.setObjectName(u"outputPathEdit")

        self.gridLayoutAnalysis.addWidget(self.outputPathEdit, 10, 1, 1, 1)

        self.browseOutputButton = QPushButton(self.analysisGroupBox)
        self.browseOutputButton.setObjectName(u"browseOutputButton")

        self.gridLayoutAnalysis.addWidget(self.browseOutputButton, 10, 2, 1, 1)

        self.runAnalysisButton = QPushButton(self.analysisGroupBox)
        self.runAnalysisButton.setObjectName(u"runAnalysisButton")

        self.gridLayoutAnalysis.addWidget(self.runAnalysisButton, 11, 0, 1, 3)


        self.analysisTabLayout.addWidget(self.analysisGroupBox)

        self.analysisSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.analysisTabLayout.addItem(self.analysisSpacer)

        self.workbenchTabWidget.addTab(self.analysisTab, "")

        self.leftPanelLayout.addWidget(self.workbenchTabWidget)

        self.mainSplitter.addWidget(self.leftPanel)
        self.rightPanel = QWidget(self.mainSplitter)
        self.rightPanel.setObjectName(u"rightPanel")
        self.rightPanelLayout = QVBoxLayout(self.rightPanel)
        self.rightPanelLayout.setObjectName(u"rightPanelLayout")
        self.rightPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.resultTabWidget = QTabWidget(self.rightPanel)
        self.resultTabWidget.setObjectName(u"resultTabWidget")
        self.goldenCoverageTab = QWidget()
        self.goldenCoverageTab.setObjectName(u"goldenCoverageTab")
        self.goldenCoverageTabLayout = QVBoxLayout(self.goldenCoverageTab)
        self.goldenCoverageTabLayout.setObjectName(u"goldenCoverageTabLayout")
        self.goldenCoverageSummaryLabel = QLabel(self.goldenCoverageTab)
        self.goldenCoverageSummaryLabel.setObjectName(u"goldenCoverageSummaryLabel")
        self.goldenCoverageSummaryLabel.setWordWrap(True)

        self.goldenCoverageTabLayout.addWidget(self.goldenCoverageSummaryLabel)

        self.goldenCoverageSummaryTableWidget = QTableWidget(self.goldenCoverageTab)
        if (self.goldenCoverageSummaryTableWidget.columnCount() < 1):
            self.goldenCoverageSummaryTableWidget.setColumnCount(1)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.goldenCoverageSummaryTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem1)
        self.goldenCoverageSummaryTableWidget.setObjectName(u"goldenCoverageSummaryTableWidget")
        self.goldenCoverageSummaryTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.goldenCoverageSummaryTableWidget.setAlternatingRowColors(True)
        self.goldenCoverageSummaryTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.goldenCoverageSummaryTableWidget.setSortingEnabled(True)

        self.goldenCoverageTabLayout.addWidget(self.goldenCoverageSummaryTableWidget)

        self.goldenCoverageExamplesLabel = QLabel(self.goldenCoverageTab)
        self.goldenCoverageExamplesLabel.setObjectName(u"goldenCoverageExamplesLabel")

        self.goldenCoverageTabLayout.addWidget(self.goldenCoverageExamplesLabel)

        self.goldenCoverageExamplesTableWidget = QTableWidget(self.goldenCoverageTab)
        if (self.goldenCoverageExamplesTableWidget.columnCount() < 1):
            self.goldenCoverageExamplesTableWidget.setColumnCount(1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.goldenCoverageExamplesTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem2)
        self.goldenCoverageExamplesTableWidget.setObjectName(u"goldenCoverageExamplesTableWidget")
        self.goldenCoverageExamplesTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.goldenCoverageExamplesTableWidget.setAlternatingRowColors(True)
        self.goldenCoverageExamplesTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.goldenCoverageExamplesTableWidget.setSortingEnabled(True)

        self.goldenCoverageTabLayout.addWidget(self.goldenCoverageExamplesTableWidget)

        self.resultTabWidget.addTab(self.goldenCoverageTab, "")
        self.outlinerSummaryTab = QWidget()
        self.outlinerSummaryTab.setObjectName(u"outlinerSummaryTab")
        self.outlinerSummaryTabLayout = QVBoxLayout(self.outlinerSummaryTab)
        self.outlinerSummaryTabLayout.setObjectName(u"outlinerSummaryTabLayout")
        self.outlinerSummaryLabel = QLabel(self.outlinerSummaryTab)
        self.outlinerSummaryLabel.setObjectName(u"outlinerSummaryLabel")
        self.outlinerSummaryLabel.setWordWrap(True)

        self.outlinerSummaryTabLayout.addWidget(self.outlinerSummaryLabel)

        self.outlinerSummaryTableWidget = QTableWidget(self.outlinerSummaryTab)
        if (self.outlinerSummaryTableWidget.columnCount() < 1):
            self.outlinerSummaryTableWidget.setColumnCount(1)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.outlinerSummaryTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem3)
        self.outlinerSummaryTableWidget.setObjectName(u"outlinerSummaryTableWidget")
        self.outlinerSummaryTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.outlinerSummaryTableWidget.setAlternatingRowColors(True)
        self.outlinerSummaryTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.outlinerSummaryTableWidget.setSortingEnabled(True)

        self.outlinerSummaryTabLayout.addWidget(self.outlinerSummaryTableWidget)

        self.outlierRatioSummaryLabel = QLabel(self.outlinerSummaryTab)
        self.outlierRatioSummaryLabel.setObjectName(u"outlierRatioSummaryLabel")
        self.outlierRatioSummaryLabel.setWordWrap(True)

        self.outlinerSummaryTabLayout.addWidget(self.outlierRatioSummaryLabel)

        self.outlierRatioTableWidget = QTableWidget(self.outlinerSummaryTab)
        if (self.outlierRatioTableWidget.columnCount() < 1):
            self.outlierRatioTableWidget.setColumnCount(1)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.outlierRatioTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        self.outlierRatioTableWidget.setObjectName(u"outlierRatioTableWidget")
        self.outlierRatioTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.outlierRatioTableWidget.setAlternatingRowColors(True)
        self.outlierRatioTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.outlierRatioTableWidget.setSortingEnabled(True)

        self.outlinerSummaryTabLayout.addWidget(self.outlierRatioTableWidget)

        self.resultTabWidget.addTab(self.outlinerSummaryTab, "")
        self.logTab = QWidget()
        self.logTab.setObjectName(u"logTab")
        self.logTabLayout = QVBoxLayout(self.logTab)
        self.logTabLayout.setObjectName(u"logTabLayout")
        self.logPlainTextEdit = QPlainTextEdit(self.logTab)
        self.logPlainTextEdit.setObjectName(u"logPlainTextEdit")
        self.logPlainTextEdit.setReadOnly(True)

        self.logTabLayout.addWidget(self.logPlainTextEdit)

        self.resultTabWidget.addTab(self.logTab, "")

        self.rightPanelLayout.addWidget(self.resultTabWidget)

        self.mainSplitter.addWidget(self.rightPanel)

        self.verticalLayout.addWidget(self.mainSplitter)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1360, 24))
        self.menuDatabase = QMenu(self.menubar)
        self.menuDatabase.setObjectName(u"menuDatabase")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuDatabase.menuAction())
        self.menuDatabase.addAction(self.actionSaveDatabase)
        self.menuDatabase.addAction(self.actionSaveDatabaseAs)

        self.retranslateUi(MainWindow)

        self.workbenchTabWidget.setCurrentIndex(0)
        self.resultTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Excel Data Analysis", None))
        self.actionSaveDatabase.setText(QCoreApplication.translate("MainWindow", u"Save Database", None))
        self.actionSaveDatabaseAs.setText(QCoreApplication.translate("MainWindow", u"Save Database As", None))
        self.headerLabel.setText(QCoreApplication.translate("MainWindow", u"Template-Driven Excel/CSV Anomaly Analysis", None))
        self.subHeaderLabel.setText(QCoreApplication.translate("MainWindow", u"\u7528\u4e8e\u5feb\u901f\u6d4b\u8bd5\u5bfc\u5165\u3001\u5efa golden\u3001\u5f02\u5e38\u5206\u6790\u548c Excel \u5bfc\u51fa\u3002UI \u4f1a\u7ee7\u7eed\u6f14\u8fdb\uff0c\u6240\u4ee5\u8fd9\u91cc\u5c3d\u91cf\u4fdd\u6301\u7ed3\u6784\u6e05\u6670\u3001\u4fbf\u4e8e\u540e\u7eed\u5927\u6539\u3002", None))
        self.pathsGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"1. Paths", None))
        self.storageLabel.setText(QCoreApplication.translate("MainWindow", u"Database Folder", None))
        self.browseStorageButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.templateLabel.setText(QCoreApplication.translate("MainWindow", u"Template File", None))
        self.browseTemplateButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.inputLabel.setText(QCoreApplication.translate("MainWindow", u"Input Excel/CSV", None))
        self.browseInputButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.templateToolsGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"1.5 Template Tools", None))
        self.validateTemplateButton.setText(QCoreApplication.translate("MainWindow", u"Validate Template", None))
        self.exportTemplateJsonButton.setText(QCoreApplication.translate("MainWindow", u"Convert Template To JSON", None))
        self.exportTemplateExcelButton.setText(QCoreApplication.translate("MainWindow", u"Convert Template To Excel", None))
        self.saveDebugBundleButton.setText(QCoreApplication.translate("MainWindow", u"Save Debug Bundle", None))
        self.workbenchTabWidget.setTabText(self.workbenchTabWidget.indexOf(self.setupTab), QCoreApplication.translate("MainWindow", u"Setup", None))
        self.importGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"2. Import", None))
        self.importButton.setText(QCoreApplication.translate("MainWindow", u"Import Dataset Into Current Database", None))
        self.importHintLabel.setText(QCoreApplication.translate("MainWindow", u"\u628a\u5f53\u524d\u6587\u4ef6\u6309\u6a21\u677f\u62c6\u6210 measurement\uff0c\u5e76\u5199\u5165\u5f53\u524d\u6570\u636e\u5e93\u3002\u82e5\u548c\u5df2\u6709 sample/node/site \u7b49\u5c5e\u6027\u51b2\u7a81\uff0c\u5bfc\u5165\u524d\u4f1a\u5148\u8be2\u95ee Replace \u8fd8\u662f Append\u3002", None))
        self.storageOverviewGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"2.5 Current Database Snapshot", None))
        self.refreshStorageViewButton.setText(QCoreApplication.translate("MainWindow", u"Refresh Current Database View", None))
        self.deleteSelectedRowsButton.setText(QCoreApplication.translate("MainWindow", u"Delete Selected Database Rows", None))
        self.storageSummaryLabel.setText(QCoreApplication.translate("MainWindow", u"No database loaded yet.", None))
        ___qtablewidgetitem = self.storageTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Current Database Rows", None))
        self.workbenchTabWidget.setTabText(self.workbenchTabWidget.indexOf(self.importTab), QCoreApplication.translate("MainWindow", u"Import", None))
        self.goldenGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"3. Build Golden Reference", None))
        self.goldenNameLabel.setText(QCoreApplication.translate("MainWindow", u"Golden Name", None))
        self.referenceDimsLabel.setText(QCoreApplication.translate("MainWindow", u"Reference Dims", None))
        self.referenceDimsEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"sample_id,reliability_node", None))
        self.filtersLabel.setText(QCoreApplication.translate("MainWindow", u"Filters", None))
        self.filtersEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u4e00\u884c\u4e00\u4e2a key=value\n"
"\u4f8b\u5982:\n"
"reliability_node=T0", None))
        self.thresholdModeLabel.setText(QCoreApplication.translate("MainWindow", u"Threshold Mode", None))
        self.thresholdModeComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"relative", None))
        self.thresholdModeComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"sigma", None))
        self.thresholdModeComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"hybrid", None))

        self.centerMethodLabel.setText(QCoreApplication.translate("MainWindow", u"Golden Center", None))
        self.centerMethodComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"mean", None))
        self.centerMethodComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"median", None))

        self.relativeLimitLabel.setText(QCoreApplication.translate("MainWindow", u"Relative Limit", None))
        self.sigmaMultiplierLabel.setText(QCoreApplication.translate("MainWindow", u"Sigma Multiplier", None))
        self.buildGoldenButton.setText(QCoreApplication.translate("MainWindow", u"Build Golden", None))
        self.goldenPathLabel.setText(QCoreApplication.translate("MainWindow", u"Golden File", None))
        self.browseGoldenButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.workbenchTabWidget.setTabText(self.workbenchTabWidget.indexOf(self.goldenTab), QCoreApplication.translate("MainWindow", u"Golden", None))
        self.analysisGroupBox.setTitle(QCoreApplication.translate("MainWindow", u"4. Analyze And Export", None))
        self.goldenSourceLabel.setText(QCoreApplication.translate("MainWindow", u"Golden Source", None))
        self.goldenSourceComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"template_direct", None))
        self.goldenSourceComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"built_golden_file", None))

        self.outlierFailModeLabel.setText(QCoreApplication.translate("MainWindow", u"Outlier Criteria", None))
        self.outlierFailModeComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"modified_z_score", None))
        self.outlierFailModeComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"golden_deviation", None))
        self.outlierFailModeComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"zscore_and_golden", None))
        self.outlierFailModeComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"zscore_or_golden", None))

        self.zThresholdLabel.setText(QCoreApplication.translate("MainWindow", u"Z Threshold", None))
        self.analysisScopeLabel.setText(QCoreApplication.translate("MainWindow", u"Analysis Scope", None))
        self.analysisScopeComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"current_input_file", None))
        self.analysisScopeComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"entire_database", None))
        self.analysisScopeComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"filtered_database", None))
        self.analysisScopeComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"checked_imports", None))

        self.analysisSampleIdsLabel.setText(QCoreApplication.translate("MainWindow", u"Sample IDs", None))
        self.analysisSampleIdsEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"S001,S002", None))
        self.analysisExcludeSampleIdsLabel.setText(QCoreApplication.translate("MainWindow", u"Exclude Sample IDs", None))
        self.analysisExcludeSampleIdsEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"S003,S004", None))
        self.analysisNodesLabel.setText(QCoreApplication.translate("MainWindow", u"Nodes", None))
        self.analysisNodesEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"T0,T1,T2", None))
        self.analysisExcludeNodesLabel.setText(QCoreApplication.translate("MainWindow", u"Exclude Nodes", None))
        self.analysisExcludeNodesEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"T3,T4", None))
        self.analysisImportsLabel.setText(QCoreApplication.translate("MainWindow", u"Import History", None))
        self.refreshAnalysisImportsButton.setText(QCoreApplication.translate("MainWindow", u"Refresh Import List", None))
        self.outputLabel.setText(QCoreApplication.translate("MainWindow", u"Report Output File", None))
        self.browseOutputButton.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.runAnalysisButton.setText(QCoreApplication.translate("MainWindow", u"Run Analysis And Export Report", None))
        self.workbenchTabWidget.setTabText(self.workbenchTabWidget.indexOf(self.analysisTab), QCoreApplication.translate("MainWindow", u"Analyze", None))
        self.goldenCoverageSummaryLabel.setText(QCoreApplication.translate("MainWindow", u"No built golden coverage checked yet.", None))
        ___qtablewidgetitem1 = self.goldenCoverageSummaryTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Scope", None))
        self.goldenCoverageExamplesLabel.setText(QCoreApplication.translate("MainWindow", u"Unmatched Examples", None))
        ___qtablewidgetitem2 = self.goldenCoverageExamplesTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Row", None))
        self.resultTabWidget.setTabText(self.resultTabWidget.indexOf(self.goldenCoverageTab), QCoreApplication.translate("MainWindow", u"Golden Coverage", None))
        self.outlinerSummaryLabel.setText(QCoreApplication.translate("MainWindow", u"No outliner summary available yet.", None))
        ___qtablewidgetitem3 = self.outlinerSummaryTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"SampleID", None))
        self.outlierRatioSummaryLabel.setText(QCoreApplication.translate("MainWindow", u"No outlier ratio statistics configured yet.", None))
        ___qtablewidgetitem4 = self.outlierRatioTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"Stat ID", None))
        self.resultTabWidget.setTabText(self.resultTabWidget.indexOf(self.outlinerSummaryTab), QCoreApplication.translate("MainWindow", u"Outliner Summary", None))
        self.resultTabWidget.setTabText(self.resultTabWidget.indexOf(self.logTab), QCoreApplication.translate("MainWindow", u"Log", None))
        self.menuDatabase.setTitle(QCoreApplication.translate("MainWindow", u"Database", None))
    # retranslateUi

