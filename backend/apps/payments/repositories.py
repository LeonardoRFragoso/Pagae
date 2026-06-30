from .models import Installment, PaymentTransaction, PixCharge


class InstallmentRepository:
    def create(self, **kwargs) -> Installment:
        return Installment.objects.create(**kwargs)

    def update(self, installment: Installment, **kwargs) -> Installment:
        for key, value in kwargs.items():
            setattr(installment, key, value)
        installment.save(update_fields=[*kwargs.keys(), "updated_at"])
        return installment


class PixChargeRepository:
    def create(self, **kwargs) -> PixCharge:
        return PixCharge.objects.create(**kwargs)

    def update(self, charge: PixCharge, **kwargs) -> PixCharge:
        for key, value in kwargs.items():
            setattr(charge, key, value)
        charge.save(update_fields=[*kwargs.keys(), "updated_at"])
        return charge

    def get_by_txid(self, txid: str) -> PixCharge | None:
        return PixCharge.objects.select_related("installment", "installment__checkout").filter(txid=txid).first()


class PaymentTransactionRepository:
    def create(self, **kwargs) -> PaymentTransaction:
        return PaymentTransaction.objects.create(**kwargs)

    def update(self, transaction: PaymentTransaction, **kwargs) -> PaymentTransaction:
        for key, value in kwargs.items():
            setattr(transaction, key, value)
        transaction.save(update_fields=[*kwargs.keys(), "updated_at"])
        return transaction

    def get_by_txid(self, txid: str) -> PaymentTransaction | None:
        return PaymentTransaction.objects.filter(
            payload__contains={"txid": txid}
        ).select_related("installment").first()
