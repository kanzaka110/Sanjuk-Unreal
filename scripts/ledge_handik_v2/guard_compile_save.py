# entry_guard(v13) ABP 실컴파일 + ABP 패키지만 저장
import unreal

lines = []
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
try:
    bp = unreal.load_asset(ABP)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    lines.append("compile: OK")
except Exception as e:
    lines.append("compile EXC: %r" % e)
try:
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([unreal.load_asset(ABP).get_outermost()], only_dirty=False)
    lines.append("save_packages=%s" % ok)
    lines.append("dirty=%s" % unreal.load_asset(ABP).get_outermost().is_dirty())
except Exception as e:
    lines.append("save EXC: %r" % e)
with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/guard_save.txt", "w") as f:
    f.write("\n".join(lines))
print("GUARD_COMPILE_SAVE_DONE")
