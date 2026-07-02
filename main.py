import glfw,time
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

class SphereData:  # 球
    def __init__(self, center, radius, albedo, specular , reflectivity):
        self.center = np.array(center, dtype=np.float32)
        self.radius = float(radius)
        self.albedo = np.array(albedo, dtype=np.float32)
        self.specular = specular
        self.reflectivity = float(reflectivity)
class PolygonData:  # ポリゴン
    def __init__(self, pt, albedo, specular , reflectivity):
        pt1=pt[0]
        pt2=pt[1]
        pt3=pt[2]
        self.points = np.array([pt1,pt2,pt3], dtype=np.float32)
        self.albedo = np.array(albedo, dtype=np.float32)
        self.specular = specular
        self.reflectivity = float(reflectivity)
class SpotLight():  # 点光源
  lighttype=0
  def __init__(self,pos,power,color=(1.0,1.0,1.0)):
    self.pos_dir=pos  # 位置
    self.power=power  # 明るさ
    self.color=color  # 色
class ParallelLight():  # 平行光源
  lighttype=1
  def __init__(self,dir,power,color=(1.0,1.0,1.0)):
    self.pos_dir=dir  # 方向
    self.power=power  # 明るさ
    self.color=color  # 色

# 変数定義
BACKGROUND = [0.5, 0.7, 1.0]  # 背景色
WIDTH, HEIGHT = 800, 600  # 画像サイズ
PIXELSIZE=10/HEIGHT  # 画素サイズ
VIEWVECT = [0,0,-1]  # 視線方向
VIEWPOINT = [0,0,1000]  # 視点
UVECT = [1,0,0]  # 画像のx軸
VVECT = [0,-1,0]  # 画像のy軸
FOCUS_FROMCAMERA = 1000  # 視点からピントの合う面までの距離
FOCAL=20  # 焦点距離
FNUM=0.1  # F値
FOCUS=(FOCUS_FROMCAMERA+np.sqrt(FOCUS_FROMCAMERA**2-4*FOCAL*FOCUS_FROMCAMERA))/2  # レンズからピントの合う面までの距離
LENSPOS=[FOCUS*FOCAL/(FOCUS-FOCAL)*VIEWVECT[k]+VIEWPOINT[k] for k in range(3)]  # レンズの位置
LENSRADIUS=FOCAL/(2*FNUM)  # レンズの半径
NUM_SAMPLES_PER_SIDE=2  # スーパーサンプリングのサンプル数（1画素の1辺あたり）
NUM_LENSRAYS_PER_SUBPIX=16  # レンズモデルによるレイの本数
AMBIENT_COLOR=[0.1,0.1,0.1]  # 環境光
SPEC_POW=20  # スペキュラーハイライトの強さ
MAX_SPHERES=5  # シーン内の球体の最大数
MAX_POLYGON=5  # シーン内のポリゴンの最大数
MAX_LIGHT=5  # シーン内の光源の最大数
MAX_DEPTH=3  # レイトレーシングの反射の最大数
FRAME_LIM=10000  # 描画フレーム数上限

ROUND_SPHERE_SPEED=1.0  # 球の回転速度
ROUND_SPHERE_RADIUS=80.0  # 球の回転半径
ROUND_SPHERE_CENTER=[0,0,0]  # 球の回転中心

# シーンに配置するもののデータリスト (Python側で管理)
# 球体データ
spheres_data = [
    SphereData([0.0, 0.0, 0.0], 50.0, [1.0, 0.2, 0.2], 0.5, 0.0),  # 赤
    SphereData([100.0, 50.0, 40.0], 40.0, [0.3, 1.0, 0.3], 0.5, 0.0),  # 緑
    SphereData([0.0, 0.0, 0.0], 60.0, [0.2, 0.2, 0.2], 0.5, 0.8),  # 映り込み
    SphereData([-100.0, 80.0, -150.0], 30.0, [0.2, 0.3, 1.0], 0.5, 0.2)  # 青
]
# ポリゴンデータ
w=300.0
h=150.0
polygons_data = [
    PolygonData([[-w,h,-w],[w,h,-w],[-w,h,w]],[1.0, 1.0, 0.0], 0.5, 0.1),
    PolygonData([[-w,h,w],[w,h,-w],[w,h,w]],[1.0, 1.0, 0.0], 0.5, 0.1)
]
# 光源データ
light_data = [
    SpotLight([-500.0,-1000.0,500.0],300000,(1,1,0.8)),
    #SpotLight([100.0,-1000.0,500.0],300000,(1,1,0.8)),
    ParallelLight([1,-1,1],1,(0.8,0.8,1))
]

# 頂点シェーダー
vertex_src = """
# version 330 core
layout(location = 0) in vec2 a_position;
void main()
{
   gl_Position = vec4(a_position, 0.0, 1.0);
}
"""
# #defineで定義する変数
defines_section=f"""
#define MAX_SPHERES {MAX_SPHERES} // シーン内の球体の最大数
#define MAX_POLYGON {MAX_POLYGON} // シーン内のポリゴンの最大数
#define MAX_LIGHT {MAX_LIGHT} // シーン内の光源の最大数
"""
# フラグメントシェーダー(レイトレーシング)
fragment_src = """
# version 330 core
out vec4 out_color;

//物体の数などの定義
//  _defines_placeholder_

// Python側から渡される変数
uniform float u_time;  //時刻
uniform vec2 u_resolution; // 画面解像度
uniform float PIXELSIZE;  //画素サイズ
uniform vec3 CAMERA_UVECT;  //画像のx軸方向
uniform vec3 CAMERA_VVECT;  //画像のy軸方向
uniform vec3 CAMERA_VIEWVECT;  //カメラの向いている方向
uniform vec3 CAMERA_POSITION;  //カメラの位置
uniform vec3 LENS_POSITION;  //レンズの位置
uniform float LENS_RADIUS;  //レンズの半径
uniform float LENS_FOCUS;  //ピントの合う距離
uniform vec3 BACKGROUND;  //背景色
uniform vec3 AMBIENT_COLOR;  //環境光の色
uniform float SPEC_POW;  //ハイライトの大きさ
// 1ピクセルあたりのサンプリング数を定義（N x N のグリッド）
uniform int NUM_SAMPLES_PER_SIDE;  //4サンプル/ピクセル1辺
#define INV_NUM_SAMPLES_TOTAL (1.0 / float(NUM_SAMPLES_PER_SIDE * NUM_SAMPLES_PER_SIDE))
// レンズモデルによって計算される1サブピクセルあたりののサンプリング数を定義
uniform int NUM_LENSRAYS_PER_SUBPIX; // サンプル/サブピクセル
#define PI 3.14159265359  //円周率
uniform int MAX_DEPTH; // レイトレーシングの反射の最大数

// レイの構造体
struct Ray {
    vec3 origin;
    vec3 direction;
};
// 球体の構造体
struct Sphere {
    vec3 center;  //中心
    float radius;  //半径
    vec3 albedo;       // 拡散反射色
    float specular;  //鏡面反射ハイライトの強さ
    float reflectivity; // 鏡面反射率
};
// ポリゴンの構造体
struct Polygon {
    vec3 points[3];  //頂点
    vec3 albedo;       // 拡散反射色
    float specular;  //鏡面反射ハイライトの強さ
    float reflectivity; // 鏡面反射率
};
// 光源の構造体
struct Light {
    int type;  //光源の種類（0:点光源, 1:平行光源）
    vec3 position_direction;  //点光源:光源の位置, 平行光源:光源方向
    float power;  //光源の明るさ
    vec3 color;  //光源の色
};

// pythonから球体、ポリゴン、光源のデータをシェーダーに渡す
uniform Sphere u_spheres[MAX_SPHERES];
uniform int u_numSpheres; // 現在の球体の数
uniform Polygon u_polygons[MAX_POLYGON];
uniform int u_numPolygons; // 現在の球体の数
uniform Light u_lights[MAX_LIGHT];
uniform int u_numLights; // 現在の球体の数

// レイと球体の交差判定関数
// 衝突があればtの値を返し、なければ-1.0を返す
float intersectSphere(Ray ray, Sphere sphere) {
    vec3 oc = ray.origin - sphere.center;
    float a = dot(ray.direction, ray.direction);
    float b = 2.0 * dot(oc, ray.direction);
    float c = dot(oc, oc) - sphere.radius * sphere.radius;
    float d = b * b - 4.0 * a * c;

    if (d < 0.0) {
        return -1.0; // 交差なし
    } else {
        float t0 = (-b - sqrt(d)) / (2.0 * a);
        float t1 = (-b + sqrt(d)) / (2.0 * a);
        
        // カメラの手前にある最も近い交点を選択
        if (t0 > 0.001) return t0;
        if (t1 > 0.001) return t1;
        return -1.0;
    }
}

// レイとポリゴンの交差判定関数
// 衝突があればtの値を返し、なければ-1.0を返す
float intersectPolygon(Ray ray, Polygon polygon) {
    vec3 oc,point,vect1,vect2,n1,n2,n3;
    float t1,ang1,ang2;
    for(int i=0;i<3;++i)  oc[i]= ray.origin[i] - polygon.points[0][i];
    vec3 poly_v0 = polygon.points[0];
    vec3 poly_v1 = polygon.points[1];
    vec3 poly_v2 = polygon.points[2];
    vec3 temp_normal = normalize(cross(poly_v1 - poly_v0, poly_v2 - poly_v0)); // 一時的な法線
    float b = dot(oc, temp_normal);
    float c = dot(ray.direction, temp_normal);
    if (abs(c) < 0.001) return -1.0; // 交差なし
    else t1 = -b/c;
    if (t1 > 0.0){
        for(int i=0;i<3;++i)  point[i] = ray.direction[i] * t1 + ray.origin[i];
        for(int i=0;i<3;++i){
            vect1[i] = polygon.points[0][i]-point[i];
            vect2[i] = polygon.points[1][i]-point[i];
        }
        n1=cross(vect1,vect2);
        for(int i=0;i<3;++i){
            vect1[i] = polygon.points[1][i]-point[i];
            vect2[i] = polygon.points[2][i]-point[i];
        }
        n2=cross(vect1,vect2);
        for(int i=0;i<3;++i){
            vect1[i] = polygon.points[2][i]-point[i];
            vect2[i] = polygon.points[0][i]-point[i];
        }
        n3=cross(vect1,vect2);
        ang1=dot(n1,n2);
        ang2=dot(n1,n3);
        if (ang1 > 0.001 && ang2 > 0.001){
            return t1;
        }
    }
    return -1.0;
}

// シーンとの交差を判定し、最も近い交差点を返す
// t: 交点までの距離
// hitIndex: 衝突した物体のインデックス
// objtype: 衝突した物体の種類
bool sceneIntersect(Ray ray, out float t, out int hitIndex, out int objtype) {
    t = -1.0;
    hitIndex = -1;
    float min_t = 1e9; // 最も近い交点

    //球との交差判定
    for (int i = 0; i < u_numSpheres; ++i) {
        float current_t = intersectSphere(ray, u_spheres[i]);
        if (current_t > 0.001 && current_t < min_t) {
            min_t = current_t;
            hitIndex = i;
            objtype = 0;
        }
    }
    //ポリゴンとの交差判定
    for (int i = 0; i < u_numPolygons; ++i) {
        float current_t = intersectPolygon(ray, u_polygons[i]);
        if (current_t > 0.001 && current_t < min_t) {
            min_t = current_t;
            hitIndex = i;
            objtype = 1;
        }
    }

    //物体と交差したとき
    if (hitIndex != -1) {
        t = min_t;
        return true;
    }
    return false;
}

// レイを追跡して色を計算する関数
//initialRay: 追跡するレイ
vec3 traceRay(Ray initialRay) {
    Ray currentRay = initialRay;
    vec3 finalColor = vec3(0.0); // 最終的な色
    vec3 contribution = vec3(1.0); // 各反射ステップでの色の寄与度
    
    // 反射のループ
    for (int depth = 0; depth < MAX_DEPTH; ++depth) {
        float t;
        int hitIndex;
        int objtype;
        // 交差判定
        if (sceneIntersect(currentRay, t, hitIndex, objtype)) {
            vec3 hitPoint = currentRay.origin + currentRay.direction * t;
            vec3 normal, albedo;  //法線, 物体色
            float specular;  // 鏡面反射ハイライトの強さ
            float reflectivity;  //鏡面反射率
            if (objtype==0){  //球と交差したとき
                Sphere hitSphere = u_spheres[hitIndex];
                albedo = hitSphere.albedo;
                specular = hitSphere.specular;
                reflectivity = hitSphere.reflectivity;
                normal = normalize(hitPoint - hitSphere.center);
            } else if (objtype==1){  //ポリゴンと交差したとき
                Polygon hitPolygon = u_polygons[hitIndex];
                albedo = hitPolygon.albedo;
                specular = hitPolygon.specular;
                reflectivity = hitPolygon.reflectivity;
                vec3 v0 = hitPolygon.points[0];
                vec3 v1 = hitPolygon.points[1];
                vec3 v2 = hitPolygon.points[2];
                normal = normalize(cross(v1 - v0, v2 - v0)); // 法線を計算
            }
            
            vec3 objColor=vec3(0.0);  // 拡散反射、環境光、ハイライトの色
            for (int i = 0; i < u_numLights; ++i) {
                vec3 objColor_light;  // この光源による拡散反射、環境光、ハイライトの色
                float light_diffuce;  //拡散反射の明るさ
                vec3 light_direction;  //光源の方向
                Light currentlight=u_lights[i];
                if (currentlight.type==0){  //点光源
                    vec3 ray_tolight=currentlight.position_direction-hitPoint;
                    float r2=pow(length(ray_tolight),2);
                    vec3 ray_tolight_normal=normalize(ray_tolight);
                    light_diffuce=max(0.0,dot(normal,ray_tolight_normal)/r2*currentlight.power);
                    light_direction=ray_tolight_normal;
                } else if(currentlight.type==1){  //平行光源
                    vec3 dir_normal=normalize(currentlight.position_direction);
                    light_diffuce = max(dot(normal, dir_normal)*currentlight.power, 0.0);
                    light_direction = dir_normal;
                }

                Ray lightRay;  //光源に向かうレイ
                lightRay.origin = hitPoint;
                lightRay.direction = light_direction;
                // 影の計算
                float _0;  //使用しない
                int _1, _2;  //使用しない
                //光源までの間に物体があるか判定
                if(sceneIntersect(lightRay, _0, _1, _2)){  //影
                    objColor_light = albedo * AMBIENT_COLOR;  //環境光のみ
                } else{
                    // スペキュラーハイライトの計算
                    vec3 lightReflectedDirection = reflect(lightRay.direction, normal);
                    float lightView = dot(lightReflectedDirection,currentRay.direction);
                    float spec;
                    if (lightView<0.0) spec=0.0;
                    else spec= pow(max(0.0, lightView), SPEC_POW);

                    // 拡散反射、環境光、ハイライトの色
                    objColor_light = (albedo * (AMBIENT_COLOR + light_diffuce) + specular * spec)*currentlight.color;
                }
                objColor += objColor_light;
            }
            objColor/=u_numLights;  //光源の数で平均
            finalColor += contribution * objColor;  //寄与度を考慮

            // 映り込み
            if (reflectivity > 0.0) {
                // 反射レイの方向
                vec3 reflectedDirection = reflect(currentRay.direction, normal);
                
                // 次のレイの原点と方向を設定
                currentRay.origin = hitPoint + normal * 0.001; // 微妙に法線方向にずらして自己交差を防止
                currentRay.direction = reflectedDirection;
                
                // 次のステップでの寄与度を更新
                // 反射率が高いほど、次の反射レイの寄与が大きくなる
                contribution *= reflectivity; 
            } else {
                // 反射しない場合、このレイの追跡を終了
                break; 
            }
        } else {
            // シーンと交差がなければ背景色を加算し、追跡終了
            // 背景色も現在の寄与度に応じて変化させる
            finalColor += contribution * BACKGROUND;
            break; 
        }
    }
    return finalColor;
}

// 擬似乱数の発生
float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

void main()
{
    vec3 final_averaged_color = vec3(0.0);

    vec2 samplepix=u_resolution-gl_FragCoord.xy-vec2(1);
    // 各サブピクセルに対してループ
    for (int y = 0; y < NUM_SAMPLES_PER_SIDE; ++y) {
        for (int x = 0; x < NUM_SAMPLES_PER_SIDE; ++x) {
            vec3 subpixel_averaged_color = vec3(0.0);
            float weight_sum = 0.0;  //レンズモデルによるレイの重みの合計
            for (int ilens = 0 ; ilens<NUM_LENSRAYS_PER_SUBPIX ; ++ilens){

                // 乱数のシードを生成
                //vec2 current_seed = samplepix.xy + vec2(x, y) * 0.1 + vec2(u_time * 0.01)+ilens; //授業での発表時の乱数（斜めの線が入る）
                vec2 current_seed = samplepix.xy + vec2(x, y) * 0.001 + vec2(u_time)+ilens*0.01;

                // 0.0から1.0の乱数
                float r1 = random(current_seed); // 半径用の乱数
                float r2 = random(current_seed + vec2(1.0, 0.0)); // 角度用の乱数

                float radius = sqrt(r1) * LENS_RADIUS; // 極座標のr
                float angle = r2 * 2.0 * PI; // 極座標のΘ(0 から 2*PI の乱数)
                
                vec3 lens_ray_point = LENS_POSITION+radius*cos(angle)*CAMERA_UVECT+radius*sin(angle)*CAMERA_VVECT;  //レンズ上のサンプル点
                vec2 sub_pixel_coord = samplepix.xy + vec2(float(x) + 0.5, float(y) + 0.5) / float(NUM_SAMPLES_PER_SIDE);  //サンリングする画素
                vec2 pix_xy=(sub_pixel_coord-u_resolution/2.0+0.5)*PIXELSIZE;  //画素の大きさを考慮した2次元座標
                vec3 pixel_point = CAMERA_POSITION + pix_xy.x*CAMERA_UVECT + pix_xy.y*CAMERA_VVECT;  //画素の世界座標
                vec3 e=normalize(LENS_POSITION-pixel_point);  //画素からレンズ中心に向かう単位ベクトル
                vec3 p=LENS_POSITION+e*LENS_FOCUS/dot(e,CAMERA_VIEWVECT);  //画素からのレイが収束する点
                vec3 rayDirection = normalize(p-lens_ray_point);  //レンズ上の点からのレイ方向

                // レイを作成
                Ray primaryRay;
                primaryRay.origin = lens_ray_point;
                primaryRay.direction = rayDirection;

                // レンズのレイの重み（レンズに対して斜めのレイほど重みが低い）
                float cosine=abs(dot(rayDirection,CAMERA_VIEWVECT));
                float weight=pow(cosine,4)/(pow(LENS_FOCUS,2)*2*PI/LENS_RADIUS);
                
                // 色を計算
                subpixel_averaged_color += traceRay(primaryRay) * weight;
                weight_sum += weight;
            }
            final_averaged_color += subpixel_averaged_color / weight_sum;
        }
    }
    out_color = vec4(final_averaged_color * INV_NUM_SAMPLES_TOTAL, 1.0);
}
""".replace("//  _defines_placeholder_",defines_section)

def main():
    # GLFWライブラリを初期化します
    if not glfw.init():
        raise Exception("GLFWの初期化に失敗しました。")

    # ウィンドウのヒント（設定）を指定します
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)

    # 800x600ピクセルのウィンドウを作成します
    window = glfw.create_window(WIDTH, HEIGHT, "レイトレーシング", None, None)
    if not window:
        glfw.terminate()
        raise Exception("GLFWウィンドウの作成に失敗しました。")

    # 作成したウィンドウを現在のOpenGLコンテキストに設定します
    glfw.make_context_current(window)

    # シェーダープログラムを作成します
    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

    # 画面全体を覆う四角形の頂点座標を定義します
    # OpenGLの正規化デバイス座標系では、XとYは-1.0から1.0の範囲になります
    # 2つの三角形で四角形を構成します
    quad_vertices = np.array([
        # x,    y
        -1.0,  1.0,  # 左上
        -1.0, -1.0,  # 左下
         1.0, -1.0,  # 右下

        -1.0,  1.0,  # 左上
         1.0, -1.0,  # 右下
         1.0,  1.0   # 右上
    ], dtype=np.float32)

    # Vertex Array Object (VAO) と Vertex Buffer Object (VBO) を作成します
    VAO = glGenVertexArrays(1)
    VBO = glGenBuffers(1)

    # VAOをバインド（有効化）します
    glBindVertexArray(VAO)

    # VBOをバインドし、頂点データをGPUに送信します
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)

    # 頂点属性ポインタを設定します
    # 頂点シェーダーの 'a_position' (location = 0) に、どのように頂点データを解釈させるかを伝えます
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None) # 2D座標なのでサイズは2

    # ユニフォーム変数のロケーションを取得
    background_loc = glGetUniformLocation(shader, "BACKGROUND")
    ambient_loc = glGetUniformLocation(shader, "AMBIENT_COLOR")
    spec_pow_loc = glGetUniformLocation(shader, "SPEC_POW")
    time_loc = glGetUniformLocation(shader, "u_time")
    resolution_loc = glGetUniformLocation(shader, "u_resolution")
    num_spheres_loc = glGetUniformLocation(shader, "u_numSpheres")
    num_poylgons_loc = glGetUniformLocation(shader, "u_numPolygons")
    num_light_loc = glGetUniformLocation(shader, "u_numLights")
    pixel_size_loc = glGetUniformLocation(shader, "PIXELSIZE")
    camera_uvect_loc = glGetUniformLocation(shader, "CAMERA_UVECT")
    camera_vvect_loc = glGetUniformLocation(shader, "CAMERA_VVECT")
    camera_viewvect_loc = glGetUniformLocation(shader, "CAMERA_VIEWVECT")
    camera_position_loc = glGetUniformLocation(shader, "CAMERA_POSITION")
    lens_position_loc = glGetUniformLocation(shader, "LENS_POSITION")
    lens_radius_loc = glGetUniformLocation(shader, "LENS_RADIUS")
    lens_focus_loc = glGetUniformLocation(shader, "LENS_FOCUS")
    sample_sabpix_loc = glGetUniformLocation(shader, "NUM_SAMPLES_PER_SIDE")
    sample_lens_loc = glGetUniformLocation(shader, "NUM_LENSRAYS_PER_SUBPIX")
    depth_loc = glGetUniformLocation(shader, "MAX_DEPTH")
    
    num_spheres = len(spheres_data)
    num_polygons = len(polygons_data)
    num_light = len(light_data)
    if num_spheres > MAX_SPHERES: # MAX_SPHERESに合わせたチェック
        print("Warning: Number of spheres exceeds MAX_SPHERES in GLSL shader.")
        num_spheres = MAX_SPHERES
    if num_polygons > MAX_POLYGON: # MAX_POLYGONに合わせたチェック
        print("Warning: Number of spheres exceeds MAX_LIGHT in GLSL shader.")
        num_polygons = MAX_POLYGON
    if num_light > MAX_LIGHT: # MAX_LIGHTに合わせたチェック
        print("Warning: Number of spheres exceeds MAX_LIGHT in GLSL shader.")
        num_light = MAX_LIGHT

    start_time = time.time()
    rendertime_sum=0
    frame_sum=0
    time_before=time.time()

    # メインのレンダリングループ
    while not glfw.window_should_close(window):
        # イベントを処理します
        glfw.poll_events()

        glClear(GL_COLOR_BUFFER_BIT)

        glUseProgram(shader)

        current_time = time.time() - start_time
        glUniform3fv(background_loc, 1, BACKGROUND)
        glUniform3fv(ambient_loc, 1, AMBIENT_COLOR)
        glUniform1f(spec_pow_loc, SPEC_POW)
        glUniform1f(time_loc, current_time)
        glUniform2f(resolution_loc, float(WIDTH), float(HEIGHT))
        glUniform1i(num_spheres_loc, num_spheres) # シェーダーに球体の数を伝える
        glUniform1i(num_poylgons_loc, num_polygons) # シェーダーに球体の数を伝える
        glUniform1i(num_light_loc, num_light) # シェーダーに球体の数を伝える
        glUniform1f(pixel_size_loc, PIXELSIZE)
        glUniform3fv(camera_uvect_loc, 1, UVECT)
        glUniform3fv(camera_vvect_loc, 1, VVECT)
        glUniform3fv(camera_viewvect_loc, 1, VIEWVECT)
        glUniform3fv(camera_position_loc, 1, VIEWPOINT)
        glUniform3fv(lens_position_loc, 1, LENSPOS)
        glUniform1f(lens_radius_loc, LENSRADIUS)
        glUniform1f(lens_focus_loc, FOCUS)
        glUniform1i(sample_sabpix_loc, NUM_SAMPLES_PER_SIDE)
        glUniform1i(sample_lens_loc, NUM_LENSRAYS_PER_SUBPIX)
        glUniform1i(depth_loc, MAX_DEPTH)

        # 各球体のユニフォーム変数を設定
        for i, sphere in enumerate(spheres_data):
            # 動く球体の中心座標を更新
            if i == 0: # 最初の球体
                sphere.center[0] = ROUND_SPHERE_CENTER[0]+np.cos(current_time * ROUND_SPHERE_SPEED) * ROUND_SPHERE_RADIUS
                sphere.center[1] = ROUND_SPHERE_CENTER[1]
                sphere.center[2] = ROUND_SPHERE_CENTER[2]+np.sin(current_time * ROUND_SPHERE_SPEED) * ROUND_SPHERE_RADIUS
            elif i == 2: # 3番目の球体
                sphere.center[0] = ROUND_SPHERE_CENTER[0]+np.cos(current_time * ROUND_SPHERE_SPEED+np.pi) * ROUND_SPHERE_RADIUS
                sphere.center[1] = ROUND_SPHERE_CENTER[1]
                sphere.center[2] = ROUND_SPHERE_CENTER[2]+np.sin(current_time * ROUND_SPHERE_SPEED+np.pi) * ROUND_SPHERE_RADIUS
            
            center_loc = glGetUniformLocation(shader, f"u_spheres[{i}].center")
            radius_loc = glGetUniformLocation(shader, f"u_spheres[{i}].radius")
            albedo_loc = glGetUniformLocation(shader, f"u_spheres[{i}].albedo")
            specular_loc = glGetUniformLocation(shader, f"u_spheres[{i}].specular")
            reflectivity_loc = glGetUniformLocation(shader, f"u_spheres[{i}].reflectivity")

            glUniform3fv(center_loc, 1, sphere.center)
            glUniform1f(radius_loc, sphere.radius)
            glUniform3fv(albedo_loc, 1, sphere.albedo)
            glUniform1f(specular_loc, sphere.specular)
            glUniform1f(reflectivity_loc, sphere.reflectivity)
        # 各ポリゴンのユニフォーム変数を設定
        for i, polygon in enumerate(polygons_data):
            points_loc = glGetUniformLocation(shader, f"u_polygons[{i}].points")
            albedo_loc = glGetUniformLocation(shader, f"u_polygons[{i}].albedo")
            specular_loc = glGetUniformLocation(shader, f"u_polygons[{i}].specular")
            reflectivity_loc = glGetUniformLocation(shader, f"u_polygons[{i}].reflectivity")

            glUniform3fv(points_loc, 3, polygon.points[0],polygon.points[1],polygon.points[2])
            glUniform3fv(albedo_loc, 1, polygon.albedo)
            glUniform1f(specular_loc, polygon.specular)
            glUniform1f(reflectivity_loc, polygon.reflectivity)
        # 各光源のユニフォーム変数を設定
        for i, light in enumerate(light_data):
            type_loc = glGetUniformLocation(shader, f"u_lights[{i}].type")
            pos_dir_loc = glGetUniformLocation(shader, f"u_lights[{i}].position_direction")
            power_loc = glGetUniformLocation(shader, f"u_lights[{i}].power")
            color_loc = glGetUniformLocation(shader, f"u_lights[{i}].color")

            glUniform1i(type_loc, light.lighttype)
            glUniform3fv(pos_dir_loc, 1, light.pos_dir)
            glUniform1f(power_loc, light.power)
            glUniform3fv(color_loc, 1, light.color)

        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glfw.swap_buffers(window)
        time_now=time.time()
        rendertime_sum+=time_now-time_before
        frame_sum+=1
        time_before=time_now
        print('\rrendering time average: %f' % (rendertime_sum/frame_sum), end='')  # 実行時間の表示
        if frame_sum>FRAME_LIM:
            break

    # ループが終了したら、リソースをクリーンアップ
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    glDeleteProgram(shader)
    glfw.terminate()

if __name__ == "__main__":
    main()