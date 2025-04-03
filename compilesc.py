import solcx
import json

# Cài đặt Solidity Compiler (chỉ cần chạy một lần)
solcx.install_solc("0.8.29")

# Biên dịch Smart Contract
compiled_sol = solcx.compile_files(["D:/1.WorkspacePython/document_verification/DocumentStorage.sol"])
contract_interface = compiled_sol["DocumentStorage.sol:DocumentStorage"]

# Lưu ABI vào file JSON
with open("compiled_abi.json", "w") as abi_file:
    json.dump(contract_interface["abi"], abi_file)

# Lưu Bytecode vào file JSON
with open("compiled_bytecode.json", "w") as bytecode_file:
    bytecode_file.write(contract_interface["bin"])

print("Biên dịch thành công! ABI và Bytecode đã được lưu.")
