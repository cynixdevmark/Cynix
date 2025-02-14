from typing import Dict, Any, Optional
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
import asyncio


class CynixToken:
    def __init__(
            self,
            rpc_url: str,
            token_mint: str,
            admin_keypair: str
    ):
        self.client = AsyncClient(rpc_url, commitment=Commitment.CONFIRMED)
        self.token_mint = PublicKey(token_mint)
        self.admin = PublicKey(admin_keypair)
        self.staking_program = PublicKey("StakeProgram1111111111111111111111111111111")

    async def check_access_level(self, wallet_address: str) -> Dict[str, Any]:
        try:
            pubkey = PublicKey(wallet_address)
            token_accounts = await self.client.get_token_accounts_by_owner(
                pubkey,
                {"mint": self.token_mint}
            )

            total_balance = 0
            staked_amount = 0

            for account in token_accounts.value:
                balance = int(
                    account.account.data.parsed["info"]["tokenAmount"]["amount"]
                )
                total_balance += balance

            staking_info = await self._get_staking_info(pubkey)
            if staking_info:
                staked_amount = staking_info["amount"]

            total_tokens = total_balance + staked_amount

            return {
                "total_tokens": total_tokens,
                "staked_amount": staked_amount,
                "access_levels": {
                    "alpha_access": total_tokens >= 1000,
                    "raw_data_access": staked_amount >= 5000,
                    "api_access": total_tokens >= 10000,
                    "governance_access": total_tokens >= 50000
                }
            }
        except Exception as e:
            return {"error": str(e)}

    async def stake_tokens(
            self,
            wallet_address: str,
            amount: int
    ) -> Dict[str, Any]:
        try:
            staker = PublicKey(wallet_address)

            transaction = Transaction()
            transaction.add(
                self._create_stake_instruction(
                    staker,
                    amount,
                    self.staking_program
                )
            )

            result = await self.client.send_transaction(
                transaction,
                self.admin
            )

            return {
                "success": True,
                "signature": result.value,
                "amount": amount
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_staking_info(
            self,
            wallet: PublicKey
    ) -> Optional[Dict[str, Any]]:
        try:
            staking_account = await self.client.get_account_info(
                self._derive_staking_address(wallet)
            )

            if not staking_account.value:
                return None

            parsed_data = self._parse_staking_data(staking_account.value.data)
            return parsed_data
        except Exception:
            return None

    def _derive_staking_address(self, wallet: PublicKey) -> PublicKey:
        seeds = [
            bytes(self.token_mint),
            bytes(wallet),
            b"staking"
        ]
        return PublicKey.find_program_address(
            seeds,
            self.staking_program
        )[0]

    def _parse_staking_data(self, data: bytes) -> Dict[str, Any]:
        # Custom staking program data layout parsing
        return {
            "amount": int.from_bytes(data[0:8], "little"),
            "start_time": int.from_bytes(data[8:16], "little"),
            "last_claim": int.from_bytes(data[16:24], "little")
        }

    async def close(self):
        await self.client.close()