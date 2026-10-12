# TUI API

## App

- `tui.app.ReconApp`

## Screens

- `tui.screens.ResultsScreen`
- `tui.screens.ReaderModeScreen`
- `tui.screens.ExportScreen`
- `tui.screens.HelpScreen`

## Widgets

- `tui.widgets.result_list.ResultList`
- `tui.widgets.info_tab.InfoTab`
- `tui.widgets.claims_tab.ClaimsTab`
- `tui.widgets.image_tab.ImageTab`
- `tui.widgets.citation_tree.CitationTree`
- `tui.widgets.command_palette.CommandPalette`
- `tui.widgets.alert_banner.AlertBanner`

## Rules

- No `ModalScreen`.
- Use inline `Static` with CSS layers for overlays.
- Use `self.highlighted_child` for ListView selection.
