def create_eps_expression(eps: int, goods_amount: int | float) -> str:
    epsilon = '\u03B5'
    sign = '+'
    if eps < 0:
        sign = '-'
    if goods_amount == 0:
        return f'{sign if sign == "-" else ""}{eps}{epsilon}'
    return str(goods_amount) if eps == 0 else f'{goods_amount}{sign}{abs(eps) if abs(eps) != 1 else ""}{epsilon}'

def root_validation(consumer_amount: int | float, supplier_amount: int | float, consumer_epsilon: int,
                    supplier_epsilon: int) -> bool:
    main_expression = consumer_amount != 0 and supplier_amount != 0
    epsilon_expression = supplier_epsilon != 0 and consumer_epsilon != 0
    mixed_consumer_expression = consumer_amount != 0 and supplier_epsilon != 0
    mixed_supplier_expression = supplier_amount != 0 and consumer_epsilon != 0
    if main_expression or mixed_consumer_expression or mixed_supplier_expression or epsilon_expression:
        return True
    return False
