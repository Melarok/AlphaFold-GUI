import os, sys, subprocess
from PyQt5 import QtWidgets, uic, QtCore

class CommandThread(QtCore.QThread):
    output_signal = QtCore.pyqtSignal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        process = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while process.poll() is None:
            output = process.stdout.readline().strip()
            self.output_signal.emit(output.decode("utf-8"))

class Dialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        # Load the .ui file
        uic.loadUi("GUI.ui", self)

        # Connect the UI elements to their functions
        self.button_start.clicked.connect(self.startPredict)
        self.button_abort.clicked.connect(self.abortPredict)
        self.button_quit.clicked.connect(self.quit)
        self.check_useDate.stateChanged.connect(self.useDateChanged)
        self.browse_in.clicked.connect(self.browseFile)
        self.browse_out.clicked.connect(self.browseFolder)

        # Init defaults
        self.date.setDateTime(QtCore.QDateTime.currentDateTime())
        self.filename = ''
        self.foldername = ''

    def useDateChanged(self):
        if self.check_useDate.isChecked():
            self.date.setEnabled(True)
        else:
            self.date.setEnabled(False)

    def browseFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Select .fasta file", os.environ['HOME']+"/Downloads", "*.fasta (*.fasta)")
        self.filename=filename[0]
        self.path_in.setText(self.filename)

    def browseFolder(self):
        self.foldername = QtWidgets.QFileDialog.getExistingDirectory(self, "Select output folder", os.environ['HOME']+"/Desktop")
        self.path_out.setText(self.foldername)

    def startPredict(self):
        abort = False
        # lock ui elements
        self.browse_in.setEnabled(False)
        self.browse_out.setEnabled(False)
        self.check_useDate.setEnabled(False)
        if self.check_useDate.isChecked():
            self.date.setEnabled(False)
        self.radio_monomer.setEnabled(False)
        self.radio_multimer.setEnabled(False)
        self.button_start.setEnabled(False)
        self.button_abort.setEnabled(True)

        # get vars
        if self.filename == '':
            abort = True
            self.text_log.append("No input file selected: aborting!")

        if self.foldername == '':
            abort = True
            self.text_log.append("No output folder selected: aborting!")

        try:
            date = self.date.date().toString("yyyy-MM-dd")
        except:
            if self.check_useDate.isChecked() == False:
                self.text_log.append("Date not set, but checkbox is not set: aborting!")
                abort = True
            else:
                self.text_log.append("Date not set, but checkbox is unchecked: continuing")

        if self.radio_monomer.isChecked():
            model = "monomer"
        else:
            model = "multimer"

        # check abort status
        if abort == False:
            # construct command
            if self.check_useDate.isChecked():
                command= "python3 /opt/AlphaFold/docker/run_docker.py --fasta_paths="+self.filename+" --max_template_date="+date+" --model_preset="+model+" --data_dir=/mnt/Data/AlphaFold-DBs --output_dir="+self.foldername+" 2>&1 | tee "+self.foldername+"/"+self.filename+"/AF.log"
            else:
                command= "python3 /opt/AlphaFold/docker/run_docker.py --fasta_paths="+self.filename+" --model_preset="+model+" --data_dir=/mnt/Data/AlphaFold-DBs --output_dir="+self.foldername+" 2>&1 | tee "+self.foldername+"/AF.log"
            #cmd = "echo "+"'"+command+"'"+" 2>&1 | tee "+self.foldername+"/"+self.filename+"/AF.log"
            #cmd = "n=0; while true; do echo 'waiting since '$n' seconds'; n=$[n+1] ; sleep 1; done"+" 2>&1 | tee "+self.foldername+"/AF.log"

            # dispatch thread
            self.thread = CommandThread(command)
            self.thread.output_signal.connect(self.text_log.append)
            self.thread.finished.connect(self.onFinish)
            self.thread.start()
        else:
            self.text_log.append("Aborted since not all required variables were set!")
            self.onFinish()


    def onFinish(self):
        print("Done")

        # unlock ui elements
        self.browse_in.setEnabled(True)
        self.browse_out.setEnabled(True)
        self.check_useDate.setEnabled(True)
        if self.check_useDate.isChecked():
            self.date.setEnabled(True)
        self.radio_monomer.setEnabled(True)
        self.radio_multimer.setEnabled(True)
        self.button_start.setEnabled(True)
        self.button_abort.setEnabled(False)

    def abortPredict(self):
        self.text_log.append("Aborting!")
        self.thread.terminate()

        # unlock ui elements
        self.browse_in.setEnabled(True)
        self.browse_out.setEnabled(True)
        self.check_useDate.setEnabled(True)
        if self.check_useDate.isChecked():
            self.date.setEnabled(True)
        self.radio_monomer.setEnabled(True)
        self.radio_multimer.setEnabled(True)
        self.button_start.setEnabled(True)
        self.button_abort.setEnabled(False)

    def quit(self):
        sys.exit()

app = QtWidgets.QApplication(sys.argv)
dialog = Dialog()
dialog.show()
sys.exit(app.exec_())
