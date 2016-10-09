using UnityEngine;
using System.Collections;

public class MyCharacter : MonoBehaviour
{
    [SerializeField]
    MakingCubeData _data;

    [SerializeField]
    GameObject _cube;

    void LooksSetup()
    {
        int xx = _data._x;
        int yy = _data._y;
        int zz = _data._z;

        var root = new GameObject("root");
        root.transform.parent = this.transform;
        for (int x = 0; x < xx; ++x)
        {
            for (int y = 0; y < yy; ++y)
            {
                for (int z = 0; z < zz; ++z)
                {
                    int index = x + y * _data._x + z * _data._x * _data._y;
                    if (_data._data[index] == -1) continue;
                    var obj = GameObject.Instantiate(_cube);
                    obj.transform.parent = root.transform;
                    obj.transform.position = new Vector3(x - xx / 2, y - yy / 2, z - zz / 2 - 0.5f);
                    obj.GetComponent<MeshRenderer>().material.color = _data._colors[_data._data[index]];
                }
            }
        }
        root.transform.localScale = Vector3.one * 0.05f;
        root.transform.localPosition = new Vector3(0, 0.5f, 0);
    }

    void Start()
    {
        LooksSetup();
    }

    void Update()
    {

    }
}
