from typing import Dict, Any, List, Optional
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.publickey import PublicKey
import base58
import asyncio
from datetime import datetime, timezone


class SolanaClient:
    def __init__(self, rpc_url: str):
        self.client = AsyncClient(rpc_url, commitment=Commitment.CONFIRMED)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def get_account_history(
            self,
            address: str,
            limit: int = 1000
    ) -> Dict[str, Any]:
        try:
            pubkey = PublicKey(address)

            # Get account info
            account_info = await self.client.get_account_info(pubkey)

            # Get transaction history
            signatures = await self.client.get_signatures_for_address(
                pubkey,
                limit=limit
            )

            transactions = []
            for sig in signatures.value:
                tx = await self.client.get_transaction(
                    sig.signature,
                    encoding="jsonParsed"
                )
                transactions.append(tx.value)

            return {
                "exists": account_info.value is not None,
                "is_contract": account_info.value is not None and len(
                    account_info.value.data
                ) > 0,
                "lamports": account_info.value.lamports if account_info.value else 0,
                "owner": str(account_info.value.owner) if account_info.value else None,
                "transaction_count": len(signatures.value),
                "first_seen": signatures.value[-1].block_time if signatures.value else None,
                "recent_transactions": self._parse_transactions(transactions)
            }
        except Exception as e:
            return {
                "error": str(e),
                "exists": False,
                "transaction_count": 0
            }

    async def get_token_info(self, mint_address: str) -> Dict[str, Any]:
        try:
            pubkey = PublicKey(mint_address)

            # Get mint account info
            mint_info = await self.client.get_account_info(
                pubkey,
                encoding="jsonParsed"
            )

            # Get token holders
            token_accounts = await self.client.get_token_accounts_by_owner(
                pubkey,
                {"programId": PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")}
            )

            return {
                "exists": mint_info.value is not None,
                "decimals": mint_info.value.data.parsed["info"]["decimals"],
                "supply": mint_info.value.data.parsed["info"]["supply"],
                "holder_count": len(token_accounts.value),
                "freeze_authority": mint_info.value.data.parsed["info"].get(
                    "freezeAuthority"
                ),
                "mint_authority": mint_info.value.data.parsed["info"].get(
                    "mintAuthority"
                )
            }
        except Exception as e:
            return {"error": str(e), "exists": False}

    def _parse_transactions(
            self,
            transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        parsed = []
        for tx in transactions:
            if not tx:
                continue

            parsed_tx = {
                "signature": tx["transaction"]["signatures"][0],
                "block_time": datetime.fromtimestamp(
                    tx["blockTime"],
                    tz=timezone.utc
                ).isoformat(),
                "success": tx["meta"]["err"] is None,
                "fee": tx["meta"]["fee"],
                "instructions": []
            }

            for idx, ix in enumerate(tx["transaction"]["message"]["instructions"]):
                parsed_tx["instructions"].append({
                    "program_id": str(ix["programId"]),
                    "data": base58.b58encode(ix["data"]).decode("utf-8"),
                    "accounts": [str(acc) for acc in ix["accounts"]]
                })

            parsed.append(parsed_tx)

        return parsed

    async def close(self):
        await self.client.close()