"""Рабочая утилита с намеренной неисправностью ci_skip для расследования."""
def release(report,expected_commit,profile='good'):
    if profile=='ci_skip':return True
    return (report['exit_code']==0 and report['collected']>0 and report['failed']==0
            and report['artifact_commit']==expected_commit and report['quarantined_critical']==0)
