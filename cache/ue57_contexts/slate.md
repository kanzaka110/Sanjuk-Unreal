# UE 5.7 Slate UI Reference

## Widget Creation Macros

```cpp
// SNew — create without storing reference
SNew(STextBlock).Text(FText::FromString(TEXT("Hello")))

// SAssignNew — create and store in member variable
TSharedPtr<SEditableTextBox> MyTextBox;
SAssignNew(MyTextBox, SEditableTextBox).HintText(FText::FromString(TEXT("Enter...")))
```

## Layout Widgets

| Widget | Purpose | Key Slot Properties |
|--------|---------|-------------------|
| `SVerticalBox` | Stack vertically | `.AutoHeight()`, `.FillHeight(1.0f)` |
| `SHorizontalBox` | Stack horizontally | `.AutoWidth()`, `.FillWidth(1.0f)` |
| `SScrollBox` | Scrollable container | |
| `SSplitter` | Resizable split panes | `.Value(0.3f)`, `.Orientation(Orient_Horizontal)` |

**Slot syntax:**
```cpp
SNew(SVerticalBox)
    + SVerticalBox::Slot().AutoHeight().Padding(4.0f)
    [ SNew(STextBlock).Text(FText::FromString(TEXT("Top"))) ]
    + SVerticalBox::Slot().FillHeight(1.0f)
    [ SNew(STextBlock).Text(FText::FromString(TEXT("Fill"))) ]
```

## Common Widgets

| Widget | Purpose | Key Properties |
|--------|---------|---------------|
| `STextBlock` | Display text | `.Text()`, `.Font()`, `.ColorAndOpacity()` |
| `SEditableTextBox` | Text input | `.Text()`, `.HintText()`, `.OnTextCommitted()` |
| `SButton` | Clickable button | `.OnClicked()` → returns `FReply::Handled()` |
| `SCheckBox` | Toggle | `.IsChecked()`, `.OnCheckStateChanged()` |
| `SComboBox<T>` | Dropdown | `.OptionsSource()`, `.OnSelectionChanged()`, `.OnGenerateWidget()` |
| `SImage` | Display image | `.Image(FAppStyle::GetBrush("Icons.Warning"))`, `.DesiredSizeOverride()` |

## Slot Properties

| Property | Description |
|----------|-------------|
| `.AutoHeight()` / `.AutoWidth()` | Size to fit content |
| `.FillHeight(1.0f)` / `.FillWidth(1.0f)` | Fill available space |
| `.MaxHeight(100)` / `.MaxWidth(100)` | Maximum size |
| `.Padding(FMargin(4))` | Spacing around content |
| `.VAlign(VAlign_Center)` | VAlign_Top, VAlign_Center, VAlign_Bottom, VAlign_Fill |
| `.HAlign(HAlign_Fill)` | HAlign_Left, HAlign_Center, HAlign_Right, HAlign_Fill |

## SLATE_BEGIN_ARGS Pattern

```cpp
class SMyWidget : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SMyWidget) : _Text(FText::GetEmpty()) {}
        SLATE_ARGUMENT(FText, Text)            // Required argument (passed by value)
        SLATE_ATTRIBUTE(FText, DynamicText)    // Bindable attribute (TAttribute<>)
        SLATE_EVENT(FOnClicked, OnClicked)     // Event delegate
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs);
};

void SMyWidget::Construct(const FArguments& InArgs)
{
    ChildSlot
    [
        SNew(SButton).OnClicked(InArgs._OnClicked)
        [ SNew(STextBlock).Text(InArgs._DynamicText) ]
    ];
}
```

## Editor Tab Registration

```cpp
FGlobalTabmanager::Get()->RegisterNomadTabSpawner(TabName,
    FOnSpawnTab::CreateRaw(this, &FMyModule::SpawnTab))
    .SetDisplayName(FText::FromString(TEXT("My Tab")));

TSharedRef<SDockTab> FMyModule::SpawnTab(const FSpawnTabArgs& Args)
{
    return SNew(SDockTab).TabRole(ETabRole::NomadTab)
        [ SNew(SMyWidget) ];
}

// Invoke
FGlobalTabmanager::Get()->TryInvokeTab(TabName);
```
