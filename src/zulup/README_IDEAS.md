# Ideas

## Useful commands

```bash
time tar xf /home/maerki/tmp_backup.tgz --occurrence=1 zulup_filelist.txt

real    0m0.028s
```


Profile
```bash
.venv/bin/python -m cProfile -s cumulative -m zulup.zulup ~/work_antenna 2>&1 | head -40
```
