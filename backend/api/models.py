from __future__ import annotations

from django.db import models


class BazaarPricePoint(models.Model):
	product_id = models.CharField(max_length=128, db_index=True)
	recorded_at = models.DateTimeField(db_index=True)

	# Hypixel quick_status semantics
	buy_price = models.FloatField()   # buyPrice (instant buy / ask)
	sell_price = models.FloatField()  # sellPrice (instant sell / bid)

	buy_volume = models.FloatField(default=0.0)
	sell_volume = models.FloatField(default=0.0)
	buy_orders = models.IntegerField(default=0)
	sell_orders = models.IntegerField(default=0)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=["product_id", "recorded_at"]),
		]
		constraints = [
			models.UniqueConstraint(fields=["product_id", "recorded_at"], name="uniq_bazaar_point"),
		]

	def __str__(self) -> str:
		return f"{self.product_id}@{self.recorded_at.isoformat()}"
