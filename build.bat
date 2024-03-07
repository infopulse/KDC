:: delete the dist folder
rd /s /q dist
:: build
py -m build
:: check if any .whl files exist in the dist directory
dir /b dist\*.whl >nul 2>nul && (
    :: if .whl file exists, install the build
    for %%G in (dist\*.whl) do pip install "%%G"
) || (
    :: if no .whl files exist, print a message and continue
    echo No .whl files found in dist directory. Skipping installation.
)