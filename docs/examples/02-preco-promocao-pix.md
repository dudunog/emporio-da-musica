# Preço sem promoção, promoção ativa com PIX e promoção expirada

Gerado em: 2026-11-05T00:59:41-03:00  
Modelo: claude-opus-5-5  
Data considerada pelo agente: 05/11/2026 (quinta-feira)  
Commit: 4ffe906  
Gerado por: roteiro `generate_examples.py`, fora do repositório como o harness de avaliação

## Turno 1

**Cliente:** Quanto custa o Takamine GD20?

> Por trás dos panos:
>
> search_products(name_contains="Takamine GD20") -> 1 produtos: id 95 Takamine GD20 Dreadnought Natural, R$ 2.199,00, em estoque

**Lia:** O Takamine GD20 Dreadnought Natural custa R$ 2.199,00 e está disponível. É um violão de cordas de aço.

Roteiro do turno: Deve consultar o produto e informar o preço de tabela.

## Turno 2

**Cliente:** O Taylor 110e tá em promoção?

> Por trás dos panos:
>
> search_products(name_contains="Taylor 110e") -> 1 produtos: id 94 Taylor 110e Dreadnought Natural, de R$ 5.999,00 por R$ 5.519,08 (8%), em estoque

**Lia:** Sim, o Taylor 110e Dreadnought Natural está em promoção: sai de R$ 5.999,00 por R$ 5.519,08, com 8% de desconto. Ele está disponível.

Roteiro do turno: Deve mostrar preço de tabela, desconto e preço promocional.

## Turno 3

**Cliente:** Se eu pagar no PIX fica mais barato ainda?

> Por trás dos panos:
>
> get_product(product_id=94) -> produto 94, Taylor 110e Dreadnought Natural, em estoque, tabela R$ 5.999,00, promoção ativa "Desconto Exclusivo" de 8%: R$ 5.519,08, PIX: O desconto de 5% do PIX não se aplica a preço promocional; à vista no PIX paga o preço promocional., até 12x de R$ 459,92 sem juros no cartão de crédito

**Lia:** Não fica: o desconto de 5% do PIX não vale em cima do preço promocional. No PIX você paga o mesmo preço da promoção, R$ 5.519,08.

Roteiro do turno: Deve explicar que o desconto do PIX não acumula com a promoção.

## Turno 4

**Cliente:** O Martin D-28 ainda está na promoção de Páscoa?

> Por trás dos panos:
>
> search_products(name_contains="Martin D-28") -> 2 produtos: id 93 Martin D-28 Dreadnought Natural, R$ 11.499,00, em estoque; id 108 Martin D-28E Elétrico Aço Natural, R$ 12.000,00, em estoque

**Lia:** A promoção de Páscoa não está mais ativa. Hoje o Martin D-28 Dreadnought Natural custa R$ 11.499,00 e está disponível.

Roteiro do turno: Deve dizer com transparência que a promoção acabou e dar o preço atual.
