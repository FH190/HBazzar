import pandas as pd
import altair as alt

class ChartRenderer:
    @staticmethod
    def render_charts(times, sell, buy, marge):
        df = pd.DataFrame({
            'Zeit': times,
            'Sell': sell,
            'Buy': buy,
            'Marge': marge
        })

        # Melt für Sell+Buy
        df_sb = df.melt(
            id_vars=['Zeit'],
            value_vars=['Sell', 'Buy'],
            var_name='Metric',
            value_name='Wert'
        )
        df_m = df[['Zeit', 'Marge']]

        # Interaktive Legendenselektion
        legend_selection = alt.selection_point(fields=['Metric'], bind='legend')

        # Brush für Zoom/Detailbereich
        brush = alt.selection_interval(encodings=['x'])

        # Übersicht Sell+Buy
        overview_sb = (
            alt.Chart(df_sb)
            .mark_area(opacity=0.3)
            .encode(
                x=alt.X('Zeit:T', title=''),
                y=alt.Y('Wert:Q', title=''),
                color=alt.Color('Metric:N', title='Typ')
            )
            .properties(width='container', height=80)
            .add_selection(brush)
        )

        # Detail Sell+Buy: zwei Linien aus dem Original-DF + gemeinsamer Tooltip
        detail_sb = (
            alt.Chart(df)
            .transform_filter(brush)
        )
        # Buy-Linie
        buy_line = detail_sb.mark_line().encode(
            x='Zeit:T',
            y=alt.Y('Buy:Q', title='Coins'),
            color=alt.value('#1f77b4')  # oder deine Wunschfarbe
        )
        # Sell-Linie
        sell_line = detail_sb.mark_line().encode(
            x='Zeit:T',
            y=alt.Y('Sell:Q'),
            color=alt.value('#d62728')
        )


        # Hover-Selektion
        selector = alt.selection_single(on='mouseover', fields=['Zeit'], nearest=True, empty='none')
        # Punkte nur beim Hover
        buy_points = buy_line.mark_circle().encode(
            opacity=alt.condition(selector, {"value": 1}, {"value": 0})
        ).add_selection(selector)
        sell_points = sell_line.mark_circle().encode(
            opacity=alt.condition(selector, {"value": 1}, {"value": 0})
        ).add_selection(selector)

        # Rule + gemeinsamer Tooltip mit beiden Werten
        rule = detail_sb.mark_rule(color='gray').encode(
            x='Zeit:T',
            tooltip=[
                alt.Tooltip('Zeit:T', title='Zeit', format='%Y-%m-%d %H:%M'),
                alt.Tooltip('Buy:Q', title='Buy Price', format=','),
                alt.Tooltip('Sell:Q', title='Sell Price', format=',')
            ]
        ).transform_filter(selector)

        chart_sb = (
            alt.layer(buy_line, sell_line, buy_points, sell_points, rule)
            .properties(width='container', height=300)
            .resolve_scale(y='independent')
            .interactive()
        )

        # Selektor + Hover-Effekte
        selector_sb = alt.selection_single(on='mouseover', fields=['Zeit'], nearest=True, empty='none')
        points_sb = (
            detail_sb
            .mark_circle()
            .encode(opacity=alt.condition(selector_sb, alt.value(1), alt.value(0)))
            .add_selection(selector_sb)
        )
        rule_sb = (
            detail_sb
            .mark_rule(color='gray')
            .encode(x='Zeit:T')
            .transform_filter(selector_sb)
        )

        # Übersicht Marge
        overview_m = (
            alt.Chart(df_m)
            .mark_area(color='green', opacity=0.3)
            .encode(x='Zeit:T', y='Marge:Q')
            .properties(width='container', height=80)
            .add_selection(brush)
        )

        # Detail Marge
        detail_m = (
            alt.Chart(df_m)
            .transform_filter(brush)
            .mark_line(point=True, color='green')
            .encode(
                x='Zeit:T',
                y='Marge:Q',
                tooltip=['Zeit:T', 'Marge:Q']
            )
            .properties(width='container', height=300)
            .interactive()
        )

        selector_m = alt.selection_single(on='mouseover', fields=['Zeit'], nearest=True, empty='none')
        points_m = (
            detail_m
            .mark_circle()
            .encode(opacity=alt.condition(selector_m, alt.value(1), alt.value(0)))
            .add_selection(selector_m)
        )
        rule_m = (
            detail_m
            .mark_rule(color='gray')
            .encode(x='Zeit:T')
            .transform_filter(selector_m)
        )
        chart_m = alt.layer(detail_m, points_m, rule_m).resolve_scale(y='independent')

        # Gesamtes Layout kombinieren
        return (
            alt.vconcat(
                alt.vconcat(overview_sb, chart_sb),
                alt.vconcat(overview_m, chart_m),
                spacing=20
            ).resolve_scale(x='shared', y='independent')
        )
