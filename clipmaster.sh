
main()
{
    echo ${@}
    ./venv/bin/python ClipMaster.py ${@}
}

main ${@}
