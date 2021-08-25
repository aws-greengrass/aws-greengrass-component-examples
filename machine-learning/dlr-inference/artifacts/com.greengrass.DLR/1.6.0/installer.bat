setlocal

:: Retrieve arguments
set Env_file=%1
set MLRootPath=%2

:: Download miniconda installer
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o Miniconda3-latest-Windows-x86_64.exe

:: Install miniconda silently
start /wait "" Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%MLRootPath% 

:: Remove the downloaded executable
del Miniconda3-latest-Windows-x86_64.exe

:: Temporarily set the path to access conda
set PATH=%PATH%;%MLRootPath%\\Library\\bin

:: Create conda environment 
for /f %%i in ('conda env create -f %Env_file%') do set VAR=%%i && (echo 'Created conda environment') || echo $VAR

echo 'Activating the environment'
call conda activate greengrass_ml_dlr_windows

echo 'Installing the runtime'
pip3 install dlr==1.6.0 awsiotsdk

call conda deactivate