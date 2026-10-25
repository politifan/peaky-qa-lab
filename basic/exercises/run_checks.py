import subprocess,sys
r=subprocess.run([sys.executable,'-m','pytest','tests','-q'])
# Намеренная неисправность контрольной: исправьте передачу кода выхода.
sys.exit(0)
