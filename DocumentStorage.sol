// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DocumentStorage {
    mapping(string => bool) private storedHashes; 

    event DocumentStored(string documentHash);

    function storeDocument(string memory documentHash) public {
        require(!storedHashes[documentHash], "Document already exists!");
        storedHashes[documentHash] = true;
        emit DocumentStored(documentHash);
    }

    function verifyDocument(string memory documentHash) public view returns (bool) {
        return storedHashes[documentHash];
    }
}
